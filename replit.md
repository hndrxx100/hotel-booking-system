# Hotel Management System

## Overview

This is a Flask-based hotel management system that provides booking functionality for guests and administrative tools for hotel staff. The system features a modern dark theme UI, real-time booking management, automated scheduling, and role-based access control.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: SQL database using SQLAlchemy with DeclarativeBase
- **Authentication**: Flask-Login for session management with role-based access (admin/receptionist)
- **Forms**: WTForms with Flask-WTF for form handling and validation
- **Scheduling**: APScheduler for background tasks (auto-cancelling unpaid bookings)

### Frontend Architecture
- **UI Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.0
- **JavaScript**: jQuery with Bootstrap components
- **CSS**: Custom styling that complements Bootstrap dark theme
- **Tables**: DataTables for enhanced table functionality
- **Date Handling**: Bootstrap Datepicker for date inputs

### Security & Middleware
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies
- **Password Security**: Werkzeug password hashing
- **Session Management**: Flask sessions with configurable secret key
- **Form Protection**: CSRF protection via Flask-WTF

## Key Components

### Models (Database Schema)
- **Staff**: User accounts with roles (admin/receptionist)
- **Guest**: Customer information and contact details
- **RoomCategory**: Room types with pricing and amenities
- **Room**: Individual rooms linked to categories
- **Booking**: Reservation records with status tracking
- **Payment**: Payment processing and status tracking (referenced but not fully implemented)

### Forms & Validation
- **Room Search**: Date validation ensuring future dates and logical date ranges
- **Booking Creation**: Guest information capture with payment method selection
- **Booking Management**: Lookup and modification capabilities
- **Admin Forms**: Staff, room, and category management (referenced)

### Route Structure
- **Public Routes**: Room search, booking creation, booking lookup
- **Admin Routes**: Dashboard, staff management, room management, reports
- **Receptionist Routes**: Limited dashboard and booking management
- **Authentication**: Login/logout with role-based redirects

### Background Processing
- **Automated Cancellation**: Unpaid bookings cancelled after 1 hour
- **Periodic Tasks**: 15-minute intervals for cleanup operations
- **Graceful Shutdown**: Proper scheduler cleanup on application exit

## Data Flow

### Booking Process
1. Guest searches for available rooms by date range
2. System queries rooms excluding those with overlapping bookings
3. Guest selects room and provides contact information
4. Booking created with unique reference number and pending status
5. Payment processing initiated (in-person or MoMo)
6. Automated cancellation scheduled if payment not received

### Room Availability Logic
- Checks room availability status (not in maintenance)
- Excludes rooms with overlapping confirmed bookings
- Supports modification scenarios by excluding current booking from conflicts
- Real-time availability calculation based on date ranges

### Administrative Workflow
- Role-based access control determines available features
- Admin users have full system access including staff management
- Receptionist users have limited access focused on daily operations
- Dashboard provides relevant metrics based on user role

## External Dependencies

### CDN Resources
- Bootstrap 5 CSS with dark theme from replit.com
- Font Awesome 6.0 for icons
- Bootstrap Datepicker for date inputs
- DataTables for enhanced table functionality
- jQuery for JavaScript functionality

### Python Packages
- Flask ecosystem (Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF)
- SQLAlchemy ORM with DeclarativeBase
- WTForms for form handling
- APScheduler for background tasks
- Werkzeug for security utilities

### Environment Configuration
- `SESSION_SECRET`: Flask session encryption key
- `DATABASE_URL`: Database connection string
- Database connection pooling with health checks configured

## Deployment Strategy

### Production Considerations
- ProxyFix middleware configured for reverse proxy deployment
- Database connection pooling with 5-minute recycling
- Connection health checks enabled (`pool_pre_ping`)
- Logging configured at DEBUG level
- WSGI-compatible application structure

### Scalability Features
- Stateless session management allows horizontal scaling
- Database connection pooling supports concurrent users
- Background task scheduling isolated from web requests
- Static assets served via CDN reduces server load

### Database Management
- Automatic table creation on application startup
- Default admin user creation if none exists
- Migration-friendly SQLAlchemy models
- Foreign key relationships properly defined

### Monitoring & Maintenance
- Comprehensive logging for debugging
- Automated cleanup of stale bookings
- Health check endpoints can be added
- Error handling throughout the application stack