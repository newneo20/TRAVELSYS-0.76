It looks like you're trying to run a Django development server along with Celery using a custom command (`runserver_with_celery`). This is not a built-in Django command, so you might need to set it up manually or use a different approach.

---

### **Option 1: If `runserver_with_celery` is a Custom Command**
If you (or someone else) created a custom management command called `runserver_with_celery`, ensure:
1. It exists in `yourapp/management/commands/runserver_with_celery.py`.
2. It properly starts both Django’s dev server and Celery.

If it’s missing, you’ll need to create it.

---

### **Option 2: Manually Run Django + Celery in Separate Terminals**
Instead of a combined command, open **two terminal windows**:

#### **Terminal 1: Django Development Server**
```bash
python manage.py runserver build.dev.travel-sys.loc:8000
```

#### **Terminal 2: Celery Worker**
```bash
celery -A your_project_name worker --loglevel=info
```
(Replace `your_project_name` with your Django project’s name, e.g., `celery -A travel_sys worker --loglevel=info`)

---

### **Option 3: Use `django-celery-beat` (For Scheduled Tasks)**
If you need Celery Beat (scheduler), run:
```bash
celery -A your_project_name beat --loglevel=info
```

---

### **Troubleshooting**
1. **Celery Not Installed?**  
   Install it first:
   ```bash
   pip install celery
   ```

2. **Redis/Broker Not Running?**  
   Ensure Redis (or your chosen broker) is running:
   ```bash
   redis-cli ping  # Should return "PONG"
   ```

3. **`runserver_with_celery` Not Found?**  
   If this is a custom script, check:
   - The file exists in `management/commands/`.
   - It imports and correctly starts Celery + Django.

---

### **Recommended Approach**
For development, running **two separate terminals** (one for Django, one for Celery) is the simplest way. If you need an automated solution, consider:
- Using `docker-compose` to manage both services.
- Creating a custom `runserver_with_celery` command (example below).

---

### **Example Custom Command (`runserver_with_celery.py`)**
If you want to create the missing command:
```python
# your_app/management/commands/runserver_with_celery.py
from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.management import call_command
import subprocess
import threading

class Command(RunserverCommand):
    help = "Runs Django dev server + Celery worker"

    def handle(self, *args, **options):
        # Start Celery in a thread
        celery_thread = threading.Thread(
            target=subprocess.call,
            args=(["celery", "-A", "your_project_name", "worker", "--loglevel=info"],),
            daemon=True,
        )
        celery_thread.start()

        # Start Django dev server
        super().handle(*args, **options)
```
Then run:
```bash
python manage.py runserver_with_celery build.dev.travel-sys.loc:8000
```

---

Let me know if you need help debugging a specific issue! 🚀