import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, abort
from config import Config
from models import db, Project, ContactMessage
from forms import ContactForm, ProjectForm, LoginForm
from utils import save_uploaded_file
from flask_mail import Mail, Message

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    # ensure instance folder exists
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    # create upload subfolders
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'projects'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'resume'), exist_ok=True)

    db.init_app(app)
    mail = Mail(app)

    # initialize db if not exists
    with app.app_context():
        db.create_all()

    # Routes
    @app.route('/')
    def index():
        projects = Project.query.order_by(Project.created_at.desc()).limit(6).all()
        return render_template('index.html', projects=projects)

    @app.route('/projects')
    def projects():
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('projects.html', projects=projects)

    @app.route('/projects/<int:project_id>')
    def project_detail(project_id):
        project = Project.query.get_or_404(project_id)
        return render_template('project_detail.html', project=project)

    @app.route('/contact', methods=['GET','POST'])
    def contact():
        form = ContactForm()
        if form.validate_on_submit():
            msg = ContactMessage(
                name=form.name.data,
                email=form.email.data,
                subject=form.subject.data,
                message=form.message.data
            )
            db.session.add(msg)
            db.session.commit()
            # Optional: send email
            try:
                if app.config.get('MAIL_SERVER'):
                    m = Message(subject=f"Portfolio contact: {form.subject.data or 'No subject'}",
                                sender=app.config.get('MAIL_DEFAULT_SENDER'),
                                recipients=[app.config.get('MAIL_DEFAULT_SENDER')])
                    m.body = f"From: {form.name.data} <{form.email.data}>\n\n{form.message.data}"
                    mail.send(m)
            except Exception as e:
                app.logger.error("Mail send failed: %s", e)
            flash("Message sent! I'll get back to you soon.", "success")
            return redirect(url_for('contact'))
        return render_template('contact.html', form=form)

    # Serve resume (static file); place resume in static/uploads/resume/resume.pdf
    @app.route('/resume')
    def resume():
        resume_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'resume')
        # list files, pick the most recent pdf or resume.pdf
        files = sorted([f for f in os.listdir(resume_dir) if f.lower().endswith('.pdf')], reverse=True)
        if not files:
            abort(404)
        return send_from_directory(resume_dir, files[0], as_attachment=True)

    # Simple admin (session based)
    def check_admin():
        return session.get('is_admin', False)

    @app.route('/admin/login', methods=['GET','POST'])
    def admin_login():
        form = LoginForm()
        if form.validate_on_submit():
            if form.username.data == os.environ.get("ADMIN_USERNAME") and form.password.data == os.environ.get("ADMIN_PASSWORD"):
                session['is_admin'] = True
                flash("Logged in as admin.", "success")
                return redirect(url_for('admin_dashboard'))
            flash("Invalid credentials.", "danger")
        return render_template('admin_login.html', form=form)

    @app.route('/admin/logout')
    def admin_logout():
        session.pop('is_admin', None)
        flash("Logged out.", "info")
        return redirect(url_for('index'))

    @app.route('/admin')
    def admin_dashboard():
        if not check_admin():
            return redirect(url_for('admin_login'))
        projects = Project.query.order_by(Project.created_at.desc()).all()
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(20).all()
        return render_template('admin_dashboard.html', projects=projects, messages=messages)

    @app.route('/admin/project/new', methods=['GET','POST'])
    def admin_new_project():
        if not check_admin():
            return redirect(url_for('admin_login'))
        form = ProjectForm()
        if form.validate_on_submit():
            filename = None
            if 'image' in request.files:
                img = request.files['image']
                if img.filename:
                    upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'projects')
                    saved = save_uploaded_file(img, upload_dir)
                    filename = saved
            p = Project(
                title=form.title.data,
                short_description=form.short_description.data,
                long_description=form.long_description.data,
                project_url=form.project_url.data,
                image_filename=filename
            )
            db.session.add(p)
            db.session.commit()
            flash("Project created.", "success")
            return redirect(url_for('admin_dashboard'))
        return render_template('project_form.html', form=form)

    @app.route('/admin/project/<int:project_id>/edit', methods=['GET','POST'])
    def admin_edit_project(project_id):
        if not check_admin():
            return redirect(url_for('admin_login'))
        project = Project.query.get_or_404(project_id)
        form = ProjectForm(obj=project)
        if form.validate_on_submit():
            project.title = form.title.data
            project.short_description = form.short_description.data
            project.long_description = form.long_description.data
            project.project_url = form.project_url.data
            if 'image' in request.files and request.files['image'].filename:
                upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'projects')
                saved = save_uploaded_file(request.files['image'], upload_dir)
                if saved:
                    project.image_filename = saved
            db.session.commit()
            flash("Project updated.", "success")
            return redirect(url_for('admin_dashboard'))
        return render_template('project_form.html', form=form, project=project)

    @app.route('/admin/project/<int:project_id>/delete', methods=['POST'])
    def admin_delete_project(project_id):
        if not check_admin():
            return redirect(url_for('admin_login'))
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        flash("Project deleted.", "info")
        return redirect(url_for('admin_dashboard'))

    
    @app.route('/add_sample_projects')
    def add_sample_projects():
        from models import Project, db

        projects = [
        Project(
            title="Advance Python Alarm Clock",
            short_description="A smart alarm clock built with Python and Tkinter.",
            long_description="Developed a smart alarm clock using Python and Tkinter with real-time clock, snooze, and custom audio control. Enhanced GUI customization and audio system integration.",
            image_filename="static/uploads/projects/alarm_clock.jpg",
            project_url="https://github.com/ravikantmaurya00/Advance-Python-Alarm-Clock"
        ),
        Project(
            title="Image Steganography using OpenCV & Tkinter",
            short_description="A GUI tool for hiding and extracting secret messages in images.",
            long_description="Built using Python, OpenCV, and Tkinter. Used bit manipulation for message embedding and extraction with a modern interface (TtkBootstrap).",
            image_filename="static/uploads/projects/steganography.jpg",
            project_url="https://github.com/ravikantmaurya00/Image-Steganography"
        ),
        Project(
            title="Network Intrusion Detection System (NIDS)",
            short_description="ML-based model for detecting malicious network traffic.",
            long_description="Implemented an ML-based model using scikit-learn and packet analysis to detect suspicious network patterns in real time.",
            image_filename="static/uploads/projects/nids.jpg",
            project_url="https://github.com/ravikantmaurya00/Network-Intrusion-Detection"
        ),
        Project(
            title="OTP Verification System",
            short_description="Secure email-based OTP authentication system.",
            long_description="Developed an OTP verification system using Python and SMTP to ensure secure user authentication.",
            image_filename="static/uploads/projects/otp_verification.jpg",
            project_url="https://github.com/ravikantmaurya00/OTP-Verification"
        ),
        Project(
            title="Cloud Deployment using Terraform & AWS",
            short_description="Automated EC2 deployment using Terraform on AWS.",
            long_description="Used Terraform for Infrastructure as Code (IaC) to deploy EC2 instances with web servers, improving deployment efficiency.",
            image_filename="static/uploads/projects/cloud_deployment.jpg",
            project_url="https://github.com/ravikantmaurya00/Cloud-Deployment"
        )
    ]

    # Insert into database
    # for p in projects:
    #     existing = Project.query.filter_by(title=p.title).first()
    #     if not existing:
    #         db.session.add(p)
    # db.session.commit()

        return "✅ Sample projects added successfully!"
    return app