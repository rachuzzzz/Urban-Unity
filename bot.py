import json
from flask import Blueprint, request, jsonify, session
import mysql.connector
from datetime import datetime

# Create a Blueprint for the chatbot API
chatbot_api = Blueprint('chatbot_api', __name__)

# Function to get database connection (reusing existing code)
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",  
        user="raisen",
        password="123456",
        database="urbanunity"
    )

# Route to handle chatbot messages
@chatbot_api.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').lower()
    
    # Check if user is logged in and what type of user they are
    user_type = None
    user_id = None
    
    if 'user_id' in session:
        user_type = 'citizen'
        user_id = session['user_id']
    elif 'admin_id' in session:
        user_type = 'admin'
        user_id = session['admin_id']
    elif 'contractor_id' in session:
        user_type = 'contractor'
        user_id = session['contractor_id']
    
    # Process the message and generate a response
    response = process_message(user_message, user_type, user_id)
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def process_message(message, user_type, user_id):
    # Intent recognition for navigation
    if any(keyword in message for keyword in ['report', 'new issue', 'new grievance']):
        return {
            'text': 'You can report a new issue by going to the "Report Issue" page.',
            'actions': [
                {
                    'type': 'navigate',
                    'url': '/report-issue',
                    'text': 'Report an Issue'
                }
            ]
        }
    
    elif any(keyword in message for keyword in ['track', 'status', 'my grievances']):
        return {
            'text': 'You can track your grievances on the tracking page.',
            'actions': [
                {
                    'type': 'navigate',
                    'url': '/track-grievance',
                    'text': 'Track Grievances'
                }
            ]
        }
    
    elif any(keyword in message for keyword in ['feedback', 'leave feedback']):
        return {
            'text': 'You can submit feedback about our services.',
            'actions': [
                {
                    'type': 'navigate',
                    'url': '/view-feedback',
                    'text': 'Submit Feedback'
                }
            ]
        }
    
    elif any(keyword in message for keyword in ['dashboard', 'home']):
        if user_type == 'citizen':
            return {
                'text': 'I can take you to your dashboard.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/citizen-dashboard',
                        'text': 'Go to Dashboard'
                    }
                ]
            }
        elif user_type == 'admin':
            return {
                'text': 'I can take you to the admin dashboard.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/manage-issues',
                        'text': 'Go to Admin Dashboard'
                    }
                ]
            }
        elif user_type == 'contractor':
            return {
                'text': 'I can take you to your contractor dashboard.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/contractor-dashboard',
                        'text': 'Go to Contractor Dashboard'
                    }
                ]
            }
    
    elif 'grievance' in message and ('find' in message or 'search' in message or 'where' in message):
        return {
            'text': 'Let me help you find information about your grievance. What\'s the ID or location of the grievance?',
            'actions': [
                {
                    'type': 'input',
                    'field': 'grievance_id',
                    'label': 'Grievance ID'
                }
            ]
        }
    
    elif message.isdigit() and user_type == 'citizen':
        # Assume user has input a grievance ID after being prompted
        grievance_id = message
        
        # Get grievance details
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, location, description, status, submitted_at
            FROM grievances
            WHERE id = %s AND user_id = %s
        """, (grievance_id, user_id))
        
        grievance = cursor.fetchone()
        cursor.close()
        db.close()
        
        if grievance:
            return {
                'text': f"Grievance #{grievance['id']} at {grievance['location']} is currently: {grievance['status']}. Would you like to see more details?",
                'actions': [
                    {
                        'type': 'navigate',
                        'url': f"/track-grievance?id={grievance['id']}",
                        'text': 'View Details'
                    }
                ]
            }
        else:
            return {
                'text': "I couldn't find a grievance with that ID. Please check the number and try again."
            }
    
    elif 'login' in message or 'sign in' in message:
        if user_type:
            return {
                'text': f"You're already logged in as a {user_type}."
            }
        else:
            return {
                'text': "You can log in as a citizen, admin, or contractor. Which one would you like?",
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/citizen-login',
                        'text': 'Citizen Login'
                    },
                    {
                        'type': 'navigate',
                        'url': '/admin-login',
                        'text': 'Admin Login'
                    },
                    {
                        'type': 'navigate',
                        'url': '/contractor-login',
                        'text': 'Contractor Login'
                    }
                ]
            }
    
    elif 'logout' in message or 'sign out' in message:
        return {
            'text': "Would you like to log out?",
            'actions': [
                {
                    'type': 'navigate',
                    'url': '/logout',
                    'text': 'Log Out'
                }
            ]
        }
    
    elif 'help' in message:
        return {
            'text': "I can help you with the following:\n- Reporting a new issue\n- Tracking your grievances\n- Navigating to your dashboard\n- Submitting feedback\n- Finding information about a specific grievance\n\nWhat would you like help with?",
        }
    
    else:
        return {
            'text': "I'm not sure I understand. You can ask me about reporting issues, tracking grievances, or navigating to different parts of the app. Type 'help' for more options."
        }

# Route to fetch grievance statistics for visualization
@chatbot_api.route('/api/grievance_stats', methods=['GET'])
def grievance_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # Get status counts for user's grievances
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM grievances
        WHERE user_id = %s
        GROUP BY status
    """, (user_id,))
    
    status_counts = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return jsonify({
        'status_counts': status_counts
    })