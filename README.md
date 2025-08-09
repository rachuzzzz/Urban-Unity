# UrbanUnity - Municipal Service Management Platform

![UrbanUnity Logo](static/images/logos.png)

## Overview

UrbanUnity is a comprehensive web-based platform that bridges the gap between citizens and municipal authorities. It enables citizens to report issues, track grievances, and engage with local government services seamlessly.

## Features

### 🏛️ For Citizens
- **Issue Reporting**: Report municipal issues with location mapping and photo uploads
- **Grievance Tracking**: Track the status of reported issues in real-time
- **Feedback System**: Provide feedback on resolved issues
- **Interactive Dashboard**: View community statistics and ongoing projects

### 👨‍💼 For Administrators
- **Issue Management**: View, filter, and manage all reported issues
- **Contractor Assignment**: Assign contractors to specific grievances
- **Task Verification**: Verify completed work and request revisions if needed
- **Analytics Dashboard**: View comprehensive statistics and charts
- **Feedback Monitoring**: Monitor citizen feedback and satisfaction ratings

### 🔧 For Contractors
- **Task Dashboard**: View assigned tasks and their priorities
- **Status Updates**: Update task progress and mark completion
- **Proof Submission**: Upload completion proofs for verification
- **Revision Management**: Handle revision requests from administrators

## Tech Stack

- **Backend**: Python Flask
- **Database**: MongoDB with PyMongo
- **File Storage**: Cloudinary for image uploads
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Maps**: Leaflet.js for location services
- **Charts**: Chart.js for analytics visualization

## Live Demo

🌐 **Live Application**: [https://urbanunity.onrender.com](https://urbanunity.onrender.com)

### Test Accounts

**Admin Login:**
- Username: `admin123`
- Password: `password123`

**Contractor Login:**
- Username: `contractor1`
- Password: `contractor123`

**Citizen:**
- Create a new account via the signup page

## Installation & Setup

### Prerequisites
- Python 3.9+
- MongoDB Atlas account
- Cloudinary account

### Environment Variables
Create a `.env` file with the following variables:

```env
SECRET_KEY=your_secret_key_here
MONGODB_URI=your_mongodb_connection_string
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/urbanunity.git
cd urbanunity
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Deployment

This application is configured for deployment on Render.com:

1. **Automatic deployment** from GitHub repository
2. **Environment variables** configured in Render dashboard
3. **Production-ready** with Gunicorn WSGI server

## Project Structure

```
urbanunity/
├── app.py                 # Main Flask application
├── bot.py                 # Chatbot functionality
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment configuration
├── static/               # Static files (CSS, JS, images)
│   └── images/
├── templates/            # HTML templates
│   ├── landing.html      # Landing page
│   ├── clogin3.html     # Citizen login
│   ├── cdashboard.html  # Citizen dashboard
│   ├── alogin.html      # Admin login
│   ├── manageissues.html # Admin dashboard
│   ├── blogin.html      # Contractor login
│   ├── contractor.html  # Contractor dashboard
│   └── ...              # Other templates
└── README.md
```

## Key Features Detail

### Issue Reporting System
- **Interactive Maps**: Click-to-select location using Leaflet.js
- **Photo Upload**: Cloudinary integration for secure image storage
- **Geolocation**: Automatic location detection with manual override
- **Real-time Validation**: Client-side and server-side form validation

### Status Tracking
- **Timeline View**: Visual progress tracking for each grievance
- **Filter Options**: Status, date range, and category filters
- **Real-time Updates**: Instant status notifications

### Admin Dashboard
- **Comprehensive Overview**: Statistics and charts for decision making
- **Contractor Management**: Assign and track contractor performance
- **Verification System**: Quality control for completed tasks

### Security Features
- **Password Hashing**: Werkzeug security for password protection
- **Session Management**: Secure user sessions with role-based access
- **Input Validation**: Protection against malicious inputs
- **CSRF Protection**: Built-in Flask security features

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

**Project Maintainer**: [Your Name]
- Email: your.email@example.com
- LinkedIn: [Your LinkedIn Profile]
- GitHub: [@yourusername](https://github.com/yourusername)

## Acknowledgments

- **Bootstrap**: For responsive UI components
- **Leaflet.js**: For interactive mapping capabilities
- **Cloudinary**: For reliable image storage and delivery
- **MongoDB**: For flexible document-based data storage
- **Render.com**: For seamless deployment and hosting

---

⭐ **Star this repository if you found it helpful!**
