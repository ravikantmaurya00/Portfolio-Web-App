import os
from werkzeug.utils import secure_filename
from uuid import uuid4

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file_storage, upload_dir):
    if not file_storage:
        return None
    if not allowed_file(file_storage.filename):
        return None
    # create folder if not exists
    os.makedirs(upload_dir, exist_ok=True)
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    new_name = f"{uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, secure_filename(new_name))
    file_storage.save(filepath)
    return os.path.relpath(filepath).replace("\\", "/")  # store relative path
