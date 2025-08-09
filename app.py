import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader
import cloudinary.api
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv
from bot import chatbot_api

# Load environment variables
load_dotenv()

# Cloudinary configuration - Production ready with environment variables
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),  
    api_key = os.getenv("CLOUDINARY_API_KEY"),  
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))
app.register_blueprint(chatbot_api)

# MongoDB connection
def get_db():
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    return client['urbanunity']

# Test database connection function
def test_db_connection():
    try:
        db = get_db()
        # Test the connection
        db.command('ping')
        print("✅ Database connection successful!")
        print(f"📊 Database name: {db.name}")
        print(f"📋 Collections: {db.list_collection_names()}")
        
        # Count documents in each collection
        for collection_name in db.list_collection_names():
            count = db[collection_name].count_documents({})
            print(f"  - {collection_name}: {count} documents")
            
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

# Home route
@app.route('/')
def home():
    return render_template('landing.html')

# Citizen Authentication Routes
@app.route('/citizen-login', methods=['GET', 'POST'])
def citizen_login():
    errors = {}
    username = ''
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Form validation
        if not username:
            errors['username'] = 'Username is required'
        if not password:
            errors['password'] = 'Password is required'
            
        if errors:
            return render_template('clogin3.html', username=username, errors=errors)

        db = get_db()
        citizens = db.citizens
        
        try:
            # Check if the username exists
            user = citizens.find_one({"username": username})
            
            if not user:
                flash("Username not found. Please check your username or sign up.", "warning")
                return render_template('clogin3.html', username=username)
            
            # Verify the hashed password
            if check_password_hash(user['password'], password):
                # Clear any existing sessions before setting new one
                session.clear()
                
                # Set new session
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                session['role'] = 'citizen'
                
                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(url_for('cdashboard'))
            else:
                flash("Incorrect password. Please try again.", "danger")
                return render_template('clogin3.html', username=username)
                
        except Exception as err:
            app.logger.error(f"Database error during login: {str(err)}")
            flash("A system error occurred. Please try again later.", "danger")
            return render_template('clogin3.html', username=username)

    return render_template('clogin3.html', username=username, errors=errors)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first-name']
        last_name = request.form['last-name']
        phone_number = request.form['phone']
        city = request.form['city']
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        citizens = db.citizens
        
        # Check if username already exists
        existing_user = citizens.find_one({"username": username})

        if existing_user:
            return render_template('clogin2.html', error="Username already exists! Try another one.")

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        # Insert into the database
        try:
            citizen_data = {
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "city": city,
                "username": username,
                "password": hashed_password,
                "created_at": datetime.utcnow()
            }
            
            citizens.insert_one(citizen_data)
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('citizen_login'))
            
        except Exception as err:
            return render_template('clogin2.html', error=f"Database error: {err}")

    return render_template('clogin2.html')

@app.route('/citizen-dashboard')
def cdashboard():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('citizen_login'))
    
    username = session['username']
    
    db = get_db()
    grievances = db.grievances
    
    # Fetch grievances of logged-in user
    user_grievances = list(grievances.find({"user_id": ObjectId(session['user_id'])}))
    
    return render_template('cdashboard.html', username=username, grievances=user_grievances)

@app.route('/track-grievance')
def track_grievance():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('citizen_login'))
    
    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date', 'all')
    
    db = get_db()
    grievances = db.grievances
    
    # Build query
    query = {"user_id": ObjectId(session['user_id'])}
    
    # Apply status filter
    if status_filter != 'all':
        query["status"] = status_filter
    
    # Apply date filter
    if date_filter != 'all':
        now = datetime.utcnow()
        if date_filter == 'week':
            query["submitted_at"] = {"$gte": now - timedelta(days=7)}
        elif date_filter == 'month':
            query["submitted_at"] = {"$gte": now - timedelta(days=30)}
        elif date_filter == 'year':
            query["submitted_at"] = {"$gte": now - timedelta(days=365)}
    
    user_grievances = list(grievances.find(query).sort("submitted_at", -1))
    
    return render_template('viewstatus.html', grievances=user_grievances)

# Admin Routes
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        government_id = request.form['government_id']
        password = request.form['password']

        if not government_id or not password:
            flash("Both Government ID and password are required", "danger")
            return render_template('alogin.html')

        db = get_db()
        government = db.government

        try:
            admin = government.find_one({"government_id": government_id})

            if admin is None:
                flash("Government ID does not exist!", "warning")
                return render_template('alogin.html')

            if check_password_hash(admin['password'], password):
                # Clear any existing sessions before setting new one
                session.clear()
                
                # Set new session
                session['admin_id'] = str(admin['_id'])
                session['government_id'] = government_id
                session['role'] = 'admin'
                
                flash(f"Welcome, {government_id}!", "success")
                return redirect(url_for('manage_issues'))
            else:
                flash("Incorrect password! Please try again.", "danger")
        
        except Exception as e:
            flash("System error occurred. Please try again.", "danger")
            app.logger.error(f"Admin login error: {e}")

    return render_template('alogin.html')

@app.route('/manage-issues')
def manage_issues():
    if 'admin_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('admin_login'))

    # Get filter parameters
    status_filter = request.args.get('status_filter', 'all')

    db = get_db()
    grievances = db.grievances
    contractors = db.contractors

    # Build query
    query = {}
    if status_filter != 'all':
        query["status"] = status_filter
    
    # Get grievances
    all_grievances = list(grievances.find(query))

    # Get tasks that need verification
    resolved_tasks = list(grievances.find({"status": "Resolved", "needs_verification": True}))

    # Count grievances by status for pie chart
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = {item['_id']: item['count'] for item in grievances.aggregate(pipeline)}

    # Fetch all contractors for dropdown
    all_contractors = list(contractors.find())

    return render_template('manageissues.html', 
                           grievances=all_grievances,
                           Resolved_tasks=resolved_tasks,
                           status_counts=status_counts, 
                           contractors=all_contractors,
                           status_filter=status_filter)

@app.route('/assign_contractor', methods=['POST'])
def assign_contractor():
    if 'admin_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('admin_login'))

    grievance_id = request.form.get('grievance_id')
    contractor_id = request.form.get('contractor_id')

    print(f"DEBUG: Assigning contractor {contractor_id} to grievance {grievance_id}")

    if grievance_id and contractor_id:
        db = get_db()
        grievances = db.grievances
        contractors = db.contractors
        
        # Verify contractor exists
        contractor = contractors.find_one({"_id": ObjectId(contractor_id)})
        if not contractor:
            flash("Selected contractor not found!", "danger")
            return redirect(url_for('manage_issues'))
        
        # Update grievance with contractor assignment
        result = grievances.update_one(
            {"_id": ObjectId(grievance_id)},
            {
                "$set": {
                    "contractor_id": ObjectId(contractor_id),
                    "status": "In Progress",
                    "assigned_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            flash(f"Contractor '{contractor['username']}' assigned successfully! Status updated to In Progress.", "success")
        else:
            flash("Failed to assign contractor. Please try again.", "danger")
    else:
        flash("Invalid grievance or contractor selection!", "danger")

    return redirect(url_for('manage_issues'))

@app.route('/verify_task', methods=['POST'])
def verify_task():
    if 'admin_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('admin_login'))
        
    task_id = request.form.get('task_id')
    
    if task_id:
        db = get_db()
        grievances = db.grievances
        
        # Update task verification
        result = grievances.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "needs_verification": False,
                    "verified_by": ObjectId(session['admin_id']),
                    "verified_at": datetime.utcnow(),
                    "status": "completed"
                }
            }
        )
        
        if result.modified_count > 0:
            flash("Task verified successfully!", "success")
        else:
            flash("Failed to verify task. Please try again.", "danger")
        
    return redirect(url_for('manage_issues'))

@app.route('/request_revision', methods=['POST'])
def request_revision():
    if 'admin_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('admin_login'))
        
    task_id = request.form.get('task_id')
    
    if task_id:
        db = get_db()
        grievances = db.grievances
        
        # Set the status back to "In Progress" and add a revision note
        result = grievances.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "status": "In Progress",
                    "revision_requested": True,
                    "needs_verification": False,
                    "revision_requested_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            flash("Revision requested. Task status changed to In Progress.", "warning")
        else:
            flash("Failed to request revision. Please try again.", "danger")
        
    return redirect(url_for('manage_issues'))

@app.route('/update_status/<string:grievance_id>', methods=['POST'])
def update_status(grievance_id):
    if 'admin_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('admin_login'))
        
    new_status = request.form.get('status')
    if new_status:
        db = get_db()
        grievances = db.grievances
        
        result = grievances.update_one(
            {"_id": ObjectId(grievance_id)},
            {"$set": {"status": new_status, "status_updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            flash(f"Status updated to {new_status}!", "success")
        else:
            flash("Failed to update status. Please try again.", "danger")
        
    return redirect(url_for('manage_issues'))

# Contractor Routes
@app.route('/contractor-login', methods=['GET', 'POST'])
def contractor_login():
    errors = {}
    username = ''
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Basic validation
        if not username:
            errors['username'] = 'Username is required'
        if not password:
            errors['password'] = 'Password is required'
            
        if errors:
            return render_template('blogin.html', username=username, errors=errors)

        db = get_db()
        contractors = db.contractors
        
        try:
            # Check contractor exists
            contractor = contractors.find_one({"username": username})
            
            if not contractor:
                flash("Username not found.", "warning")
                return render_template('blogin.html', username=username)
            
            # Verify password
            if check_password_hash(contractor['password'], password):
                session.clear()
                session['contractor_id'] = str(contractor['_id'])
                session['contractor_username'] = contractor['username']
                session['role'] = 'contractor'
                flash(f"Welcome, {contractor['username']}!", "success")
                return redirect(url_for('contractor_dashboard'))
            else:
                flash("Incorrect password.", "danger")
                return render_template('blogin.html', username=username)
                
        except Exception as err:
            app.logger.error(f"Database error: {err}")
            flash("System error. Please try again.", "danger")
            return render_template('blogin.html', username=username)

    return render_template('blogin.html', username=username, errors=errors)

@app.route('/contractor-dashboard')
def contractor_dashboard():
    if 'contractor_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('contractor_login'))
    
    username = session['contractor_username']
    contractor_id = ObjectId(session['contractor_id'])
    
    # Get filter parameters
    status_filter = request.args.get('status_filter', 'all')
    
    db = get_db()
    grievances = db.grievances
    
    # Build query for assigned tasks
    query = {"contractor_id": contractor_id}
    if status_filter != 'all':
        query["status"] = status_filter
        
    # Get tasks
    tasks = list(grievances.find(query))
    
    # Find tasks that need revision
    revision_requests = list(grievances.find({
        "contractor_id": contractor_id,
        "status": "In Progress",
        "revision_requested": True
    }))
    
    # Count tasks by status
    pipeline = [
        {"$match": {"contractor_id": contractor_id}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "in_progress": {
                    "$sum": {"$cond": [{"$eq": ["$status", "In Progress"]}, 1, 0]}
                },
                "pending_verification": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Resolved"]}, 1, 0]}
                },
                "completed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                }
            }
        }
    ]
    
    counts_result = list(grievances.aggregate(pipeline))
    counts = counts_result[0] if counts_result else {
        "total": 0, "in_progress": 0, "pending_verification": 0, "completed": 0
    }
    
    # Get completed tasks
    completed_tasks_list = list(grievances.find({
        "contractor_id": contractor_id,
        "status": "completed"
    }))
    
    return render_template('contractor.html', 
                          username=username, 
                          tasks=tasks, 
                          completed_tasks_list=completed_tasks_list,
                          revision_requests=revision_requests,
                          assigned_tasks=counts['total'],
                          in_progress_tasks=counts['in_progress'],
                          pending_verification_tasks=counts['pending_verification'],
                          completed_tasks=counts['completed'],
                          status_filter=status_filter)

@app.route('/update_task_status', methods=['POST'])
def update_task_status():
    if 'contractor_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('contractor_login'))
    
    task_id = request.form.get('task_id')
    new_status = request.form.get('status')
    completion_proof = request.files.get('completion_proof')

    if not task_id or not new_status:
        flash("Missing required data!", "danger")
        return redirect(url_for('contractor_dashboard'))

    db = get_db()
    grievances = db.grievances

    try:
        # Upload completion proof to Cloudinary if provided
        proof_url = None
        if completion_proof and completion_proof.filename:
            upload_result = cloudinary.uploader.upload(completion_proof)
            proof_url = upload_result['secure_url']

        if new_status == 'Resolved':
            update_data = {
                "status": "Resolved",
                "needs_verification": True,
                "revision_requested": False,
                "completed_at": datetime.utcnow()
            }
            if proof_url:
                update_data["completion_proof_url"] = proof_url
                
            result = grievances.update_one(
                {
                    "_id": ObjectId(task_id),
                    "contractor_id": ObjectId(session['contractor_id'])
                },
                {"$set": update_data}
            )
        else:
            result = grievances.update_one(
                {
                    "_id": ObjectId(task_id),
                    "contractor_id": ObjectId(session['contractor_id'])
                },
                {"$set": {"status": new_status, "status_updated_at": datetime.utcnow()}}
            )
        
        if result.modified_count > 0:
            flash("Task marked as Resolved and sent for admin verification!", "success")
        else:
            flash("Failed to update task status. Please try again.", "danger")
            
    except Exception as e:
        flash(f"Error updating task: {str(e)}", "danger")

    return redirect(url_for('contractor_dashboard'))

# Grievance Management Routes
@app.route('/report-issue')
def report_issue():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('citizen_login'))
    
    return render_template('report1.html')

@app.route('/submit-grievance', methods=['POST'])
def submit_grievance():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('citizen_login'))

    user_id = ObjectId(session['user_id'])
    location = request.form.get('location')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    description = request.form.get('description')
    photo = request.files.get('photo')

    if not all([location, latitude, longitude, description]):
        flash("All fields are required!", "danger")
        return redirect(url_for('report_issue'))
        
    # Fetch phone number from the citizen collection
    db = get_db()
    citizens = db.citizens
    grievances = db.grievances
    
    citizen = citizens.find_one({"_id": user_id})
    
    if not citizen:
        flash("Error retrieving user information!", "danger")
        return redirect(url_for('report_issue'))
        
    phone = citizen['phone_number']

    # Upload image to Cloudinary
    photo_url = None
    if photo and photo.filename:
        try:
            upload_result = cloudinary.uploader.upload(photo)
            photo_url = upload_result['secure_url']
        except Exception as e:
            flash(f"Error uploading image: {str(e)}", "danger")

    try:
        grievance_data = {
            "user_id": user_id,
            "location": location,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "description": description,
            "phone": phone,
            "photo_path": photo_url,
            "status": "pending",
            "submitted_at": datetime.utcnow(),
            "needs_verification": False,
            "revision_requested": False
        }
        
        result = grievances.insert_one(grievance_data)
        print(f"DEBUG: Grievance inserted with ID: {result.inserted_id}")
        flash("Grievance submitted successfully!", "success")
        
    except Exception as err:
        print(f"DEBUG: Error inserting grievance: {err}")
        flash(f"Database error: {err}", "danger")

    return redirect(url_for('cdashboard'))

# Feedback Routes
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('citizen_login'))
        
    user_id = ObjectId(session['user_id'])
    feedback_text = request.form.get('feedback_text')
    rating = request.form.get('rating')
    
    # Basic validation
    if not feedback_text:
        flash("Feedback text is required!", "danger")
        return redirect(url_for('view_feedback'))
    
    if rating:
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                flash("Rating must be between 1 and 5", "danger")
                return redirect(url_for('view_feedback'))
        except ValueError:
            flash("Rating must be a number", "danger")
            return redirect(url_for('view_feedback'))
    
    db = get_db()
    feedback = db.feedback
    
    try:
        feedback_data = {
            "user_id": user_id,
            "feedback_text": feedback_text,
            "rating": rating,
            "submitted_at": datetime.utcnow()
        }
        
        feedback.insert_one(feedback_data)
        flash("Thank you for your feedback!", "success")
    except Exception as err:
        flash(f"Database error: {err}", "danger")
    
    return redirect(url_for('cdashboard'))

@app.route('/view-feedback')
def view_feedback():
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('citizen_login'))
    
    username = session['username']
    
    # Get user's past feedback
    db = get_db()
    feedback = db.feedback
    
    user_feedback = list(feedback.find(
        {"user_id": ObjectId(session['user_id'])}
    ).sort("submitted_at", -1))
    
    return render_template('feedback.html', username=username, user_feedback=user_feedback)

# Admin view for all feedback
@app.route('/admin-feedback')
def admin_feedback():
    if 'admin_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('admin_login'))
    
    # Get filter parameters
    rating_filter = request.args.get('rating', 'all')
    date_filter = request.args.get('date', 'all')
    
    db = get_db()
    feedback = db.feedback
    citizens = db.citizens
    
    # Build aggregation pipeline
    pipeline = [
        {
            "$lookup": {
                "from": "citizens",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "citizen"
            }
        },
        {"$unwind": "$citizen"}
    ]
    
    # Apply filters
    match_conditions = {}
    if rating_filter != 'all':
        match_conditions["rating"] = int(rating_filter)
    
    if date_filter != 'all':
        now = datetime.utcnow()
        if date_filter == 'today':
            match_conditions["submitted_at"] = {"$gte": now.replace(hour=0, minute=0, second=0, microsecond=0)}
        elif date_filter == 'week':
            match_conditions["submitted_at"] = {"$gte": now - timedelta(days=7)}
        elif date_filter == 'month':
            match_conditions["submitted_at"] = {"$gte": now - timedelta(days=30)}
    
    if match_conditions:
        pipeline.append({"$match": match_conditions})
    
    pipeline.append({"$sort": {"submitted_at": -1}})
    
    all_feedback = list(feedback.aggregate(pipeline))
    
    # Calculate statistics
    stats_pipeline = [
        {
            "$group": {
                "_id": None,
                "total_count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
                "five_star": {"$sum": {"$cond": [{"$eq": ["$rating", 5]}, 1, 0]}},
                "four_star": {"$sum": {"$cond": [{"$eq": ["$rating", 4]}, 1, 0]}},
                "three_star": {"$sum": {"$cond": [{"$eq": ["$rating", 3]}, 1, 0]}},
                "two_star": {"$sum": {"$cond": [{"$eq": ["$rating", 2]}, 1, 0]}},
                "one_star": {"$sum": {"$cond": [{"$eq": ["$rating", 1]}, 1, 0]}}
            }
        }
    ]
    
    stats_result = list(feedback.aggregate(stats_pipeline))
    stats = stats_result[0] if stats_result else {
        "total_count": 0, "avg_rating": 0, "five_star": 0,
        "four_star": 0, "three_star": 0, "two_star": 0, "one_star": 0
    }
    
    return render_template(
        'feedbackview.html', 
        all_feedback=all_feedback, 
        stats=stats,
        rating_filter=rating_filter,
        date_filter=date_filter
    )

# Authentication Management
@app.route('/logout')
def logout():
    try:
        # Check if user is actually logged in before attempting logout
        if 'user_id' in session or 'admin_id' in session or 'contractor_id' in session:
            # Store the role for the success message
            role = session.get('role', 'user')
            
            # Clear all session data
            session.clear()
            
            # Success message
            flash(f"Logged out successfully!", "success")
        else:
            # User wasn't logged in
            flash("No active session to log out from.", "warning")
            
        return redirect(url_for('home'))
        
    except Exception as e:
        # Log the error
        app.logger.error(f"Error during logout: {str(e)}")
        
        # Clear session anyway as a precaution
        try:
            session.clear()
        except:
            pass
            
        # Inform the user
        flash("An error occurred during logout. Please try again or contact support if the issue persists.", "danger")
        return redirect(url_for('home'))

# Database initialization function
def init_db():
    """Initialize the database with sample data"""
    db = get_db()
    
    # Create sample admin user
    government = db.government
    if government.count_documents({}) == 0:
        admin_data = {
            "government_id": "admin123",
            "password": generate_password_hash("password123"),
            "created_at": datetime.utcnow()
        }
        government.insert_one(admin_data)
        print("✅ Sample admin user created: admin123 / password123")
    
    # Create sample contractors - FIXED VERSION
    contractors = db.contractors
    if contractors.count_documents({}) == 0:
        contractor_data = {
            "username": "contractor1",
            "password": generate_password_hash("contractor123"),
            "services_provided": "Road Maintenance, Water Supply",
            "contact_info": "+1234567890",
            "created_at": datetime.utcnow()
        }
        result = contractors.insert_one(contractor_data)
        print(f"✅ Sample contractor created: contractor1 / contractor123 (ID: {result.inserted_id})")
        
        # Create additional contractors for testing
        additional_contractors = [
            {
                "username": "contractor2",
                "password": generate_password_hash("contractor123"),
                "services_provided": "Electrical Work, Street Lighting",
                "contact_info": "+1234567891",
                "created_at": datetime.utcnow()
            },
            {
                "username": "contractor3",
                "password": generate_password_hash("contractor123"),
                "services_provided": "Waste Management, Cleaning",
                "contact_info": "+1234567892",
                "created_at": datetime.utcnow()
            }
        ]
        
        for contractor in additional_contractors:
            result = contractors.insert_one(contractor)
            print(f"✅ Additional contractor created: {contractor['username']} / contractor123 (ID: {result.inserted_id})")

if __name__ == '__main__':
    print("🚀 Starting Urban Unity Application...")
    
    # Test database connection first
    print("\n📊 Testing MongoDB connection...")
    if not test_db_connection():
        print("❌ Could not connect to MongoDB. Please check your .env file and MongoDB Atlas connection.")
        # Don't exit in production, let the app start anyway
        pass
    
    print("\n🔧 Initializing database with sample data...")
    # Initialize database with sample data
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
    
    print("\n🎯 Your app is ready! Test with these accounts:")
    print("   👨‍💼 Admin: admin123 / password123")
    print("   🔨 Contractor: contractor1 / contractor123")
    print("   🔨 Contractor: contractor2 / contractor123") 
    print("   🔨 Contractor: contractor3 / contractor123")
    print("   👤 Citizens: Create new accounts via signup")
    
    # Production-ready server configuration
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)