PrepEligible — Campus Placement & Eligibility CheckerPrepEligible is a full-stack web application I built as part of my internship project. The main idea is to help students and TPO staff manage the campus placement process more easily. Instead of manually checking each student's eligibility for every company, this system does it automatically in real-time.

What This Project Does
In most colleges, students have to manually check if they are eligible for a company visiting campus. This takes time and often causes confusion. So I built this portal where:
Students can login, fill their academic details, and instantly see which companies they are eligible for
TPO Admin can post new companies with eligibility criteria and manage all student applications from one place

Features I Built
For Students
Eligibility Check — Automatically checks CGPA, 10th marks, 12th marks, active backlogs, and branch against every company's requirements
Academic Profile — Students can update their details and upload their resume in PDF or DOC format
Eligibility Breakdown — Shows exactly which criteria passed or failed for each company
Application Tracking — Students can apply to eligible companies and track their status like Applied, Shortlisted, Selected, or Rejected

For TPO Admin
Dashboard — Shows total students, companies, applications, placement rate and average CGPA
Student Registry — View all registered students with search and filter options
Company Manager — Post new job opportunities with criteria like minimum CGPA, backlog limit, allowed branches, package, and deadline
Application Review — View student resumes, check their profiles, and update application status

New Features I Added
PDF/DOC Resume Upload — Students can upload their resume directly instead of pasting a Google Drive link. Admin can download and view it anytime
Email Notifications — When admin posts a new company, the system automatically checks all students and sends email notification to only the eligible ones. Also if a student updates their CGPA and becomes newly eligible for a company, they get notified automatically

Project Folder Structure
placement-eligibility-checker
│
├── app.py            # Main backend file, all API routes
├── db_init.py        # Creates database tables and adds sample data
├── run.py            # Starts the server and opens browser automatically
├── emails_sent.log   # Logs all email notifications sent
├── uploads/          # Stores uploaded student resumes
│
└── static/
    ├── index.html    # Main frontend page
    ├── css/
    │   └── style.css
    └── js/
        └── app.js

   //How to Run This Project
Step 1 — Make sure Python is installed:
python --version
Step 2 — Install required libraries:
pip install flask werkzeug
Step 3 — Start the project:
python run.py

How Eligibility is Calculated
The system checks 5 things for each student against each company:
Student CGPA must be greater than or equal to company minimum CGPA
Student 10th percentage must meet company requirement
Student 12th percentage must meet company requirement
Student active backlogs must be within company limit
Student branch must be in company allowed branches list

If all 5 pass, student is shown as Eligible. If even one fails, it shows exactly which criteria failed.

Email Notification Logic
Since I don't have a real SMTP server configured, emails are logged to emails_sent.log file. This file acts as proof that the notification system is working. In a real deployment, just adding SMTP credentials in environment variables would make it send actual emails.
The log file shows:
Which student was notified
Their CGPA
Which company triggered the notification
Package and deadline details
Exact timestamp

This project was developed as part of my Full Stack Web Development internship to solve a real problem faced by placement cells in engineering colleges.
























