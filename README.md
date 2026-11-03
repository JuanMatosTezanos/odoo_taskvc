Overview
Manage is a custom Odoo module designed to support Scrum-based project management. It allows users to manage projects, histories (user stories), tasks, bugs, improvements, sprints, developers, and technologies.

This project began as a tutorial implementation and was later enhanced with additional functionality including access code validation, immutable access codes, automatic developer categorization, active sprint detection, and technology logo automation.

Features
Developer Management
The module extends Odoo's built-in res.partner model to represent developers.

Additional fields include:

Last Login Date
Developer Flag (is_dev)
Access Code
Developers can be assigned to:

Technologies
Tasks
Bugs
Improvements
Access Code Validation
Developer access codes must:

Start with exactly 8 digits
End with one or more letters
Examples:

Valid:

12345678A

12345678ABC

Invalid:

ABC12345

12345A

123456789

Validation is performed using a regular expression and enforced with Odoo constraints.

Access Code Integrity
Access codes are protected after creation.

Once an access code has been assigned to a developer it cannot be modified.

A database-level uniqueness constraint also prevents duplicate access codes.

Automatic Developer Categorization
When a contact is marked as a developer (is_dev = True), the system automatically assigns the contact to the Devs category.

If the category does not exist, it is created automatically.

Project Management
Projects are the top-level organizational unit.

Each project contains:

Name
Description
Histories
History Management
Histories represent Scrum User Stories.

Each history contains:

Name
Description
Related Project
Assigned Tasks
Technology Aggregation
A computed field automatically gathers all technologies used by tasks that belong to a history.

This provides a quick overview of technologies involved in a user story.

Task Management
Tasks represent individual work items.

Each task contains:

Name
Description
Project
History
Sprint
Developers
Technologies
Start Date
End Date
Automatic Task Codes
Each task automatically generates a unique code.

Examples:

TSK_1

TSK_2

TSK_3

The code is generated using the record's database identifier.

Automatic Sprint Assignment
Tasks automatically determine which sprint they belong to based on:

Associated Project
Sprint Start Date
Sprint End Date
If an active sprint exists, the task is linked automatically.

Bug Tracking
Bugs inherit functionality from the Task model.

Additional bug features include:

Linked Tasks
Linked Bugs
Linked Improvements
Assigned Developers
Technology Associations
This allows defects to be tracked alongside development work.

Improvement Tracking
Improvements also inherit from the Task model.

They are used to represent:

Enhancements
Optimizations
Feature Requests
Improvements can be assigned to developers and technologies.

Sprint Management
Sprints organize project work into Scrum iterations.

Sprint fields include:

Project
Duration
Start Date
End Date
Assigned Tasks
Automatic End Date Calculation
Sprint end dates are calculated automatically:

end_date = start_date + duration
Active Sprint Detection
A sprint is considered active when:

Current date is after the sprint start date
Current date is before the sprint end date
This removes the need for manually activating or deactivating sprints.

Technology Management
Technologies are used to track frameworks, tools, and platforms used throughout the project.

Each technology contains:

Name
Description
Image
Automatic Logo Loading
When a technology name is entered, the system searches for a matching image file and automatically loads it into the image field.

Example:

Docker
Automatically loads:

Docker.png
The image is encoded using Base64 and stored in Odoo's image field.

Odoo Concepts Demonstrated
This project demonstrates:

Model Inheritance
Examples:

res.partner
manage.task
Relationships
One2many
Many2one
Many2many
Computed Fields
Used for:

Sprint Detection
Active Sprint Status
Technology Aggregation
Task Code Generation
Constraints
Used for:

Access Code Validation
Developer Validation
SQL Constraints
Used to enforce unique access codes.

Onchange Methods
Used for:

Technology Logo Loading
Developer Category Assignment
Custom Enhancements
The following features were added beyond the original tutorial:

Access code validation using regular expressions
Unique developer access codes
Immutable access codes
Automatic developer categorization
Dynamic sprint activity detection
Automatic technology logo loading
Technology aggregation for histories
Future Improvements
Potential enhancements include:

Burndown Charts
Velocity Tracking
Developer Workload Dashboards
Project Analytics
Email Notifications
Advanced Bug Prioritization
User Authentication with Access Codes
Author
Custom Scrum Project Management module developed in Odoo using:

Python
Odoo ORM
XML Views
Model Inheritance
Computed Fields
Constraints
Scrum Methodology Concepts
