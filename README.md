# ExamDutyManager

ExamDutyManager is a Django-based web application for managing automatic exam invigilation duty allocation with constraints.

## Tech Stack

- Python 3
- Django (latest 5.x)
- SQLite (default Django database)
- HTML + CSS with Bootstrap 5

## Features

- Admin panel to manage:
  - Faculty (with designations and quotas)
  - PhD Scholars
  - Classrooms (with capacities)
  - Exam schedules (date, time slot, time window, classrooms, expected students)
- Automatic duty allocation algorithm:
  - Per room: either 1 Professor **or** 1 Assistant Professor + 2 PhD Scholars
  - No overlapping duties per person for the same date & time slot
  - Simple gap rule: at most one duty per person per exam date
  - UFM history used to de-prioritise staff with higher UFM counts
  - Basic classroom capacity check vs expected students
- Detained alert system:
  - Round 1 (Doubt round): capacity sufficient
  - Round 2 (Question paper shortage): expected students exceed total capacity
- Clean Bootstrap dashboard UI
- CSV export of final duty allocation table

## Project Structure

- `manage.py` – Django management entry point
- `ExamDutyManager/`
  - `settings.py` – Django settings
  - `urls.py` – Root URL configuration
  - `wsgi.py`, `asgi.py` – Deployment entry points
- `allocation/` – Core application
  - `models.py` – `Faculty`, `PhDScholar`, `Classroom`, `ExamSchedule`, `DutyAllocation`, `UFMRecord`
  - `services.py` – Duty allocation algorithm
  - `views.py` – Dashboard, CRUD pages, run allocation, allocation result, CSV export
  - `forms.py` – Model and helper forms
  - `urls.py` – App-level URL configuration
  - `admin.py` – Django admin registrations
- `templates/`
  - `base.html` – Global layout with Bootstrap navigation
  - `allocation/*.html` – Feature pages
- `static/css/styles.css` – Simple styling overrides

## Setup Instructions

1. **Create and activate a virtual environment (recommended):**

   ```bash
   cd Mini_Project
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations:**

   ```bash
   python manage.py migrate
   ```

4. **Create a superuser (for Django admin):**

   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**

   ```bash
   python manage.py runserver
   ```

6. **Access the application:**

   - Dashboard: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## Usage Flow

1. Log in to the Django admin and add:
   - Faculty with their `designation` and `duty_quota`
   - PhD Scholars with `max_duties`
   - Classrooms with `capacity`
2. From the web UI:
   - Add faculty, PhD scholars, and classrooms (optional, if not using admin directly)
   - Create exam schedules with:
     - `course_name`, `date`, `time_slot` (Morning/Evening), `start_time`, `end_time`
     - `expected_students`
     - associated `classrooms`
3. Navigate to **Auto Allocation**, choose an exam, and run the allocation.
4. Review the **Duty Allocation Result** table and export it to CSV if needed.

## Notes

- The allocation logic focuses on:
  - Avoiding overlapping duties for the same date & time slot
  - Providing a simple gap rule per exam date
  - Using UFM record counts to balance duty assignments over time
- You can extend `UFMRecord` and the allocation function to implement more complex rotation or exclusion logic as needed.

