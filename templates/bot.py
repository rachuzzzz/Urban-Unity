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
    # --- COMMON COMMANDS FOR ALL USERS ---
    
    # Help command: customized based on user type
    if 'help' in message:
        if user_type == 'citizen':
            return {
                'text': "I can help you with the following:\n- Reporting a new issue\n- Tracking your grievances\n- Navigating to your dashboard\n- Submitting feedback\n- Finding information about a specific grievance\n- Logging out\n\nWhat would you like help with?",
            }
        elif user_type == 'admin':
            return {
                'text': "I can help you with the following:\n- Navigating to the issue management dashboard\n- Viewing citizen feedback\n- Managing grievances\n- Assigning contractors\n- Verifying completed tasks\n- Logging out\n\nWhat would you like help with?",
            }
        elif user_type == 'contractor':
            return {
                'text': "I can help you with the following:\n- Navigating to your dashboard\n- Updating task status\n- Viewing assigned tasks\n- Managing revisions\n- Logging out\n\nWhat would you like help with?",
            }
        else:
            return {
                'text': "I can help you with navigating the Urban Unity system. Please log in first to access personalized assistance.",
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
    
    # Logout command for all user types
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
    
    # Login command for non-logged in users
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
    
    # Dashboard navigation for all user types
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
        else:
            return {
                'text': "Please log in first to access your dashboard.",
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/citizen-login',
                        'text': 'Login'
                    }
                ]
            }
    
    # --- CITIZEN-SPECIFIC COMMANDS ---
    
    if user_type == 'citizen':
        # Report issue command
        if any(keyword in message for keyword in ['report', 'new issue', 'new grievance', 'submit issue']):
            return {
                'text': 'You can report a new issue on the Report Issue page.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/report-issue',
                        'text': 'Report an Issue'
                    }
                ]
            }
        
        # Track grievances command
        elif any(keyword in message for keyword in ['track', 'status', 'my grievances', 'view status']):
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
        
        # Feedback command
        elif any(keyword in message for keyword in ['feedback', 'leave feedback', 'submit feedback', 'give feedback']):
            return {
                'text': 'You can submit feedback about our services on the feedback page.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/view-feedback',
                        'text': 'Submit Feedback'
                    }
                ]
            }
        
        # Find grievance by ID command
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
        
        # Process grievance ID input
        elif message.isdigit():
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
    
    # --- ADMIN-SPECIFIC COMMANDS ---
    
    elif user_type == 'admin':
        # Manage issues command
        if any(keyword in message for keyword in ['manage issues', 'issues', 'grievances', 'view issues']):
            return {
                'text': 'I can take you to the issue management page.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/manage-issues',
                        'text': 'Manage Issues'
                    }
                ]
            }
        
        # View feedback command
        elif any(keyword in message for keyword in ['feedback', 'view feedback', 'citizen feedback']):
            return {
                'text': 'You can view all citizen feedback on the feedback management page.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/admin-feedback',
                        'text': 'View Feedback'
                    }
                ]
            }
        
        # Verification tasks command
        elif any(keyword in message for keyword in ['verify', 'verification', 'completed tasks', 'resolve']):
            return {
                'text': 'You can view tasks that need verification on the issues management page. I\'ll filter to show only resolved tasks.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/manage-issues?status_filter=Resolved',
                        'text': 'View Tasks Needing Verification'
                    }
                ]
            }
        
        # Assign contractors command
        elif any(keyword in message for keyword in ['assign', 'contractor', 'delegate']):
            return {
                'text': 'You can assign contractors to grievances on the issue management page.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/manage-issues',
                        'text': 'Assign Contractors'
                    }
                ]
            }
    
    # --- CONTRACTOR-SPECIFIC COMMANDS ---
    
    elif user_type == 'contractor':
        # View assigned tasks command
        if any(keyword in message for keyword in ['tasks', 'my tasks', 'assigned', 'view tasks']):
            return {
                'text': 'You can view your assigned tasks on your dashboard.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/contractor-dashboard',
                        'text': 'View Tasks'
                    }
                ]
            }
        
        # Update task status command
        elif any(keyword in message for keyword in ['update', 'status', 'complete', 'mark complete']):
            return {
                'text': 'You can update task status on your dashboard. Would you like to view tasks that need attention?',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/contractor-dashboard?status_filter=In Progress',
                        'text': 'View In-Progress Tasks'
                    }
                ]
            }
        
        # View revision requests command
        elif any(keyword in message for keyword in ['revision', 'revise', 'fix']):
            return {
                'text': 'You can view tasks that need revision on your dashboard.',
                'actions': [
                    {
                        'type': 'navigate',
                        'url': '/contractor-dashboard',
                        'text': 'View Revision Requests'
                    }
                ]
            }
    
    # Default response if no pattern is matched
    return {
        'text': "I'm not sure I understand. You can ask me about navigating the application, or type 'help' to see what I can assist you with."
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