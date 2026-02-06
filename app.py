from flask import Flask, render_template, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, TimeField, DecimalField, SelectField, validators
from config import Config

app = Flask(__name__)
app.config['MYSQL_HOST'] = Config.MYSQL_HOST
app.config['MYSQL_USER'] = Config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = Config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = Config.MYSQL_DB
app.secret_key = "supersecretkey"

mysql = MySQL(app)

# --- FORMS ---

class LocationForm(FlaskForm):
    City = StringField('City', [validators.InputRequired(), validators.Length(max=50)])
    District = StringField('District', [validators.InputRequired(), validators.Length(max=50)])
    State = StringField('State', [validators.InputRequired(), validators.Length(max=50)])

class DisasterForm(FlaskForm):
    D_type = SelectField('Disaster Type', choices=[
        ('Flood','Flood'),('Cyclone','Cyclone'),('Earthquake','Earthquake'),
        ('Landslide','Landslide'),('Fire','Fire'),('Other','Other')
    ])
    D_date = DateField('Date', format='%Y-%m-%d')
    D_time = TimeField('Time', format='%H:%M')
    Location_ID = IntegerField('Location ID', [validators.InputRequired()])

class ReliefCampForm(FlaskForm):
    Camp_Name = StringField('Camp Name', [validators.InputRequired(), validators.Length(max=100)])
    Location = StringField('Location', [validators.InputRequired(), validators.Length(max=100)])
    Capacity = IntegerField('Capacity', [validators.InputRequired(), validators.NumberRange(min=1)])
    Incharge = StringField('Incharge', [validators.InputRequired(), validators.Length(max=100)])

class VictimForm(FlaskForm):
    Vic_name = StringField('Name', [validators.InputRequired(), validators.Length(max=100)])
    DOB = DateField('Date of Birth', format='%Y-%m-%d')
    Contact = StringField('Contact', [validators.InputRequired(), validators.Length(max=15)])
    Disaster_ID = IntegerField('Disaster ID', [validators.InputRequired()])
    Camp_ID = IntegerField('Camp ID (optional)', [validators.Optional()])

class VolunteersForm(FlaskForm):
    V_name = StringField('Name', [validators.InputRequired(), validators.Length(max=100)])
    Age = IntegerField('Age', [validators.InputRequired(), validators.NumberRange(min=18)])
    Gender = SelectField('Gender', choices=[('Male','Male'), ('Female','Female'), ('Other','Other')])
    Contact_Info = StringField('Contact', [validators.InputRequired(), validators.Length(max=15)])

class ResourcesForm(FlaskForm):
    R_name = StringField('Resource Name', [validators.InputRequired(), validators.Length(max=100)])
    R_type = StringField('Resource Type', [validators.InputRequired(), validators.Length(max=50)])
    Quantity = IntegerField('Quantity', [validators.InputRequired(), validators.NumberRange(min=1)])

class RescueTeamForm(FlaskForm):
    Team_name = StringField('Team Name', [validators.InputRequired(), validators.Length(max=100)])
    Team_type = SelectField('Team Type', choices=[('Medical','Medical'),('Rescue','Rescue'),('Army','Army'),('Fire','Fire'),('Other','Other')])
    No_of_People = IntegerField('Number of People', [validators.InputRequired(), validators.NumberRange(min=1)])
    Disaster_ID = IntegerField('Disaster ID', [validators.InputRequired()])

class DonorForm(FlaskForm):
    Donor_name = StringField('Donor Name', [validators.InputRequired(), validators.Length(max=100)])
    Contact = StringField('Contact', [validators.InputRequired(), validators.Length(max=15)])

class DonationForm(FlaskForm):
    Donor_ID = IntegerField('Donor ID', [validators.InputRequired()])
    Amount = DecimalField('Amount', [validators.InputRequired(), validators.NumberRange(min=0.01)])
    Donation_date = DateField('Donation Date', format='%Y-%m-%d')
    Resource_ID = IntegerField('Resource ID', [validators.InputRequired()])

def fetch_all(query, args=None):
    cur = mysql.connection.cursor()
    cur.execute(query, args or ())
    rows = cur.fetchall()
    cur.close()
    return rows

def fetch_one(query, args):
    cur = mysql.connection.cursor()
    cur.execute(query, args)
    row = cur.fetchone()
    cur.close()
    return row

def execute_commit(query, args):
    cur = mysql.connection.cursor()
    cur.execute(query, args)
    mysql.connection.commit()
    cur.close()

# DASHBOARD + LIVE DONATIONS BOX

@app.route('/')
def dashboard():
    counts = {
        'locations': fetch_one("SELECT COUNT(*) FROM Location", ())[0],
        'disasters': fetch_one("SELECT COUNT(*) FROM Disaster", ())[0],
        'relief_camps': fetch_one("SELECT COUNT(*) FROM Relief_Camp", ())[0],
        'victims': fetch_one("SELECT COUNT(*) FROM Victim", ())[0],
        'volunteers': fetch_one("SELECT COUNT(*) FROM Volunteers", ())[0],
        'resources': fetch_one("SELECT COUNT(*) FROM Resources", ())[0],
        'rescue_teams': fetch_one("SELECT COUNT(*) FROM Rescue_Team", ())[0],
        'donors': fetch_one("SELECT COUNT(*) FROM Donor", ())[0],
        'donations': fetch_one("SELECT COUNT(*) FROM Donation", ())[0],
    }
    total_donations = fetch_one("SELECT IFNULL(SUM(Amount),0) FROM Donation", ())[0]
    return render_template('dashboard.html', counts=counts, total_donations=total_donations)

# LOCATIONS
@app.route('/location')
def location_list():
    rows = fetch_all("SELECT * FROM Location ORDER BY Location_ID ASC")
    return render_template('location.html', rows=rows)

@app.route('/location/add', methods=['GET', 'POST'])
def location_add():
    form = LocationForm()
    if form.validate_on_submit():
        try:
            execute_commit("INSERT INTO Location (City, District, State) VALUES (%s,%s,%s)", (form.City.data, form.District.data, form.State.data))
            flash('Location added successfully.', 'success')
            return redirect(url_for('location_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Location')

@app.route('/location/edit/<int:id>', methods=['GET', 'POST'])
def location_edit(id):
    row = fetch_one("SELECT * FROM Location WHERE Location_ID=%s", (id,))
    if not row:
        flash("Location not found", "danger")
        return redirect(url_for('location_list'))
    form = LocationForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit("UPDATE Location SET City=%s, District=%s, State=%s WHERE Location_ID=%s", (form.City.data, form.District.data, form.State.data, id))
            flash('Location updated successfully.', 'success')
            return redirect(url_for('location_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.City.data, form.District.data, form.State.data = row[1], row[2], row[3]
    return render_template('form.html', form=form, title='Edit Location')

@app.route('/location/delete/<int:id>', methods=['POST'])
def location_delete(id):
    try:
        execute_commit("DELETE FROM Location WHERE Location_ID=%s", (id,))
        flash('Location deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('location_list'))

# DISASTERS
@app.route('/disaster')
def disaster_list():
    rows = fetch_all("SELECT * FROM Disaster ORDER BY Disaster_ID ASC")
    return render_template('disaster.html', rows=rows)

@app.route('/disaster/add', methods=['GET', 'POST'])
def disaster_add():
    form = DisasterForm()
    if form.validate_on_submit():
        try:
            execute_commit("INSERT INTO Disaster (D_type, D_date, D_time, Location_ID) VALUES (%s,%s,%s,%s)", (form.D_type.data, form.D_date.data, form.D_time.data, form.Location_ID.data))
            flash('Disaster added successfully', 'success')
            return redirect(url_for('disaster_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Disaster')

@app.route('/disaster/edit/<int:id>', methods=['GET', 'POST'])
def disaster_edit(id):
    row = fetch_one("SELECT * FROM Disaster WHERE Disaster_ID=%s", (id,))
    if not row:
        flash("Disaster not found", "danger")
        return redirect(url_for('disaster_list'))
    form = DisasterForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit("UPDATE Disaster SET D_type=%s, D_date=%s, D_time=%s, Location_ID=%s WHERE Disaster_ID=%s", (form.D_type.data, form.D_date.data, form.D_time.data, form.Location_ID.data, id))
            flash('Disaster updated successfully.', 'success')
            return redirect(url_for('disaster_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.D_type.data, form.D_date.data, form.D_time.data, form.Location_ID.data = row[1], row[2], row[3], row[4]
    return render_template('form.html', form=form, title='Edit Disaster')

@app.route('/disaster/delete/<int:id>', methods=['POST'])
def disaster_delete(id):
    try:
        execute_commit("DELETE FROM Disaster WHERE Disaster_ID=%s", (id,))
        flash('Disaster deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('disaster_list'))

# RELIEF CAMPS
@app.route('/relief_camp')
def relief_camp_list():
    rows = fetch_all("SELECT * FROM Relief_Camp ORDER BY Camp_ID ASC")
    return render_template('relief_camp.html', rows=rows)

@app.route('/relief_camp/add', methods=['GET', 'POST'])
def relief_camp_add():
    form = ReliefCampForm()
    if form.validate_on_submit():
        try:
            execute_commit("INSERT INTO Relief_Camp (Camp_Name, Location, Capacity, Incharge) VALUES (%s,%s,%s,%s)",
                (form.Camp_Name.data, form.Location.data, form.Capacity.data, form.Incharge.data))
            flash('Relief Camp added successfully', 'success')
            return redirect(url_for('relief_camp_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Relief Camp')

@app.route('/relief_camp/edit/<int:id>', methods=['GET', 'POST'])
def relief_camp_edit(id):
    row = fetch_one("SELECT * FROM Relief_Camp WHERE Camp_ID=%s", (id,))
    if not row:
        flash("Relief Camp not found", "danger")
        return redirect(url_for('relief_camp_list'))
    form = ReliefCampForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit("UPDATE Relief_Camp SET Camp_Name=%s, Location=%s, Capacity=%s, Incharge=%s WHERE Camp_ID=%s",
                (form.Camp_Name.data, form.Location.data, form.Capacity.data, form.Incharge.data, id))
            flash('Relief Camp updated successfully.', 'success')
            return redirect(url_for('relief_camp_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.Camp_Name.data, form.Location.data, form.Capacity.data, form.Incharge.data = row[1], row[2], row[3], row[4]
    return render_template('form.html', form=form, title='Edit Relief Camp')

@app.route('/relief_camp/delete/<int:id>', methods=['POST'])
def relief_camp_delete(id):
    try:
        execute_commit("DELETE FROM Relief_Camp WHERE Camp_ID=%s", (id,))
        flash('Relief Camp deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('relief_camp_list'))

# VICTIMS - AGE HIDDEN
@app.route('/victim')
def victim_list():
    rows = fetch_all("SELECT * FROM Victim ORDER BY Victim_ID ASC")
    return render_template('victim.html', rows=rows)

@app.route('/victim/add', methods=['GET', 'POST'])
def victim_add():
    form = VictimForm()
    if form.validate_on_submit():
        try:
            camp_id = form.Camp_ID.data if form.Camp_ID.data else None
            execute_commit("INSERT INTO Victim (Vic_name, DOB, Contact, Disaster_ID, Camp_ID) VALUES (%s,%s,%s,%s,%s)",
                (form.Vic_name.data, form.DOB.data, form.Contact.data, form.Disaster_ID.data, camp_id))
            flash('Victim added successfully', 'success')
            return redirect(url_for('victim_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Victim')

@app.route('/victim/edit/<int:id>', methods=['GET', 'POST'])
def victim_edit(id):
    row = fetch_one("SELECT * FROM Victim WHERE Victim_ID=%s", (id,))
    if not row:
        flash("Victim not found", "danger")
        return redirect(url_for('victim_list'))
    form = VictimForm(obj=row)
    if form.validate_on_submit():
        try:
            camp_id = form.Camp_ID.data if form.Camp_ID.data else None
            execute_commit("UPDATE Victim SET Vic_name=%s, DOB=%s, Contact=%s, Disaster_ID=%s, Camp_ID=%s WHERE Victim_ID=%s",
                (form.Vic_name.data, form.DOB.data, form.Contact.data, form.Disaster_ID.data, camp_id, id))
            flash('Victim updated successfully', 'success')
            return redirect(url_for('victim_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.Vic_name.data, form.DOB.data, form.Contact.data, form.Disaster_ID.data, form.Camp_ID.data = row[1], row[2], row[4], row[5], row[6]
    return render_template('form.html', form=form, title='Edit Victim')

@app.route('/victim/delete/<int:id>', methods=['POST'])
def victim_delete(id):
    try:
        execute_commit("DELETE FROM Victim WHERE Victim_ID=%s", (id,))
        flash('Victim deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('victim_list'))

# VOLUNTEERS
@app.route('/volunteers')
def volunteers_list():
    rows = fetch_all("SELECT * FROM Volunteers ORDER BY Volunteer_ID ASC")
    return render_template('volunteers.html', rows=rows)

@app.route('/volunteers/add', methods=['GET', 'POST'])
def volunteers_add():
    form = VolunteersForm()
    if form.validate_on_submit():
        try:
            execute_commit(
                "INSERT INTO Volunteers (V_name, Age, Gender, Contact_Info) VALUES (%s,%s,%s,%s)",
                (form.V_name.data, form.Age.data, form.Gender.data, form.Contact_Info.data)
            )
            flash('Volunteer added successfully', 'success')
            return redirect(url_for('volunteers_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Volunteer')

@app.route('/volunteers/edit/<int:id>', methods=['GET', 'POST'])
def volunteers_edit(id):
    row = fetch_one("SELECT * FROM Volunteers WHERE Volunteer_ID=%s", (id,))
    if not row:
        flash("Volunteer not found", "danger")
        return redirect(url_for('volunteers_list'))
    form = VolunteersForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit(
                "UPDATE Volunteers SET V_name=%s, Age=%s, Gender=%s, Contact_Info=%s WHERE Volunteer_ID=%s",
                (form.V_name.data, form.Age.data, form.Gender.data, form.Contact_Info.data, id)
            )
            flash('Volunteer updated successfully', 'success')
            return redirect(url_for('volunteers_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.V_name.data, form.Age.data, form.Gender.data, form.Contact_Info.data = row[1], row[2], row[3], row[4]
    return render_template('form.html', form=form, title='Edit Volunteer')

@app.route('/volunteers/delete/<int:id>', methods=['POST'])
def volunteers_delete(id):
    try:
        execute_commit("DELETE FROM Volunteers WHERE Volunteer_ID=%s", (id,))
        flash('Volunteer deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('volunteers_list'))

# RESOURCES
@app.route('/resources')
def resources_list():
    rows = fetch_all("SELECT * FROM Resources ORDER BY Resource_ID ASC")
    return render_template('resources.html', rows=rows)

@app.route('/resources/add', methods=['GET', 'POST'])
def resources_add():
    form = ResourcesForm()
    if form.validate_on_submit():
        try:
            execute_commit(
                "INSERT INTO Resources (R_name, R_type, Quantity) VALUES (%s,%s,%s)",
                (form.R_name.data, form.R_type.data, form.Quantity.data)
            )
            flash('Resource added successfully', 'success')
            return redirect(url_for('resources_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Resource')

@app.route('/resources/edit/<int:id>', methods=['GET', 'POST'])
def resources_edit(id):
    row = fetch_one("SELECT * FROM Resources WHERE Resource_ID=%s", (id,))
    if not row:
        flash("Resource not found", "danger")
        return redirect(url_for('resources_list'))
    form = ResourcesForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit("UPDATE Resources SET R_name=%s, R_type=%s, Quantity=%s WHERE Resource_ID=%s",
                (form.R_name.data, form.R_type.data, form.Quantity.data, id))
            flash('Resource updated successfully', 'success')
            return redirect(url_for('resources_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.R_name.data, form.R_type.data, form.Quantity.data = row[1], row[2], row[3]
    return render_template('form.html', form=form, title='Edit Resource')

@app.route('/resources/delete/<int:id>', methods=['POST'])
def resources_delete(id):
    try:
        execute_commit("DELETE FROM Resources WHERE Resource_ID=%s", (id,))
        flash('Resource deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('resources_list'))

# RESCUE TEAMS
@app.route('/rescue_team')
def rescue_team_list():
    rows = fetch_all("SELECT * FROM Rescue_Team ORDER BY Team_ID ASC")
    return render_template('rescue_team.html', rows=rows)

@app.route('/rescue_team/add', methods=['GET', 'POST'])
def rescue_team_add():
    form = RescueTeamForm()
    if form.validate_on_submit():
        try:
            execute_commit("INSERT INTO Rescue_Team (Team_name, Team_type, No_of_People, Disaster_ID) VALUES (%s,%s,%s,%s)",
                (form.Team_name.data, form.Team_type.data, form.No_of_People.data, form.Disaster_ID.data))
            flash('Rescue Team added successfully', 'success')
            return redirect(url_for('rescue_team_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Rescue Team')

@app.route('/rescue_team/edit/<int:id>', methods=['GET', 'POST'])
def rescue_team_edit(id):
    row = fetch_one("SELECT * FROM Rescue_Team WHERE Team_ID=%s", (id,))
    if not row:
        flash("Rescue Team not found", "danger")
        return redirect(url_for('rescue_team_list'))
    form = RescueTeamForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit("UPDATE Rescue_Team SET Team_name=%s, Team_type=%s, No_of_People=%s, Disaster_ID=%s WHERE Team_ID=%s",
                (form.Team_name.data, form.Team_type.data, form.No_of_People.data, form.Disaster_ID.data, id))
            flash('Rescue Team updated successfully', 'success')
            return redirect(url_for('rescue_team_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.Team_name.data, form.Team_type.data, form.No_of_People.data, form.Disaster_ID.data = row[1], row[2], row[3], row[4]
    return render_template('form.html', form=form, title='Edit Rescue Team')

@app.route('/rescue_team/delete/<int:id>', methods=['POST'])
def rescue_team_delete(id):
    try:
        execute_commit("DELETE FROM Rescue_Team WHERE Team_ID=%s", (id,))
        flash('Rescue Team deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('rescue_team_list'))

# DONORS
@app.route('/donor')
def donor_list():
    rows = fetch_all("SELECT * FROM Donor ORDER BY Donor_ID ASC")
    return render_template('donor.html', rows=rows)

@app.route('/donor/add', methods=['GET', 'POST'])
def donor_add():
    form = DonorForm()
    if form.validate_on_submit():
        try:
            execute_commit("INSERT INTO Donor (Donor_name, Contact) VALUES (%s,%s)", (form.Donor_name.data, form.Contact.data))
            flash('Donor added successfully', 'success')
            return redirect(url_for('donor_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Donor')

@app.route('/donor/edit/<int:id>', methods=['GET', 'POST'])
def donor_edit(id):
    row = fetch_one("SELECT * FROM Donor WHERE Donor_ID=%s", (id,))
    if not row:
        flash("Donor not found", "danger")
        return redirect(url_for('donor_list'))
    form = DonorForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit("UPDATE Donor SET Donor_name=%s, Contact=%s WHERE Donor_ID=%s", (form.Donor_name.data, form.Contact.data, id))
            flash('Donor updated successfully', 'success')
            return redirect(url_for('donor_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.Donor_name.data, form.Contact.data = row[1], row[2]
    return render_template('form.html', form=form, title='Edit Donor')

@app.route('/donor/delete/<int:id>', methods=['POST'])
def donor_delete(id):
    try:
        execute_commit("DELETE FROM Donor WHERE Donor_ID=%s", (id,))
        flash('Donor deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('donor_list'))

# DONATIONS
@app.route('/donation')
def donation_list():
    rows = fetch_all("SELECT * FROM Donation ORDER BY Donation_ID ASC")
    return render_template('donation.html', rows=rows)

@app.route('/donation/add', methods=['GET', 'POST'])
def donation_add():
    form = DonationForm()
    if form.validate_on_submit():
        try:
            execute_commit("INSERT INTO Donation (Donor_ID, Amount, Donation_date, Resource_ID) VALUES (%s,%s,%s,%s)",
                (form.Donor_ID.data, form.Amount.data, form.Donation_date.data, form.Resource_ID.data))
            flash('Donation added successfully', 'success')
            return redirect(url_for('donation_list'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('form.html', form=form, title='Add Donation')

@app.route('/donation/edit/<int:id>', methods=['GET', 'POST'])
def donation_edit(id):
    row = fetch_one("SELECT * FROM Donation WHERE Donation_ID=%s", (id,))
    if not row:
        flash("Donation not found", "danger")
        return redirect(url_for('donation_list'))
    form = DonationForm(obj=row)
    if form.validate_on_submit():
        try:
            execute_commit("UPDATE Donation SET Donor_ID=%s, Amount=%s, Donation_date=%s, Resource_ID=%s WHERE Donation_ID=%s",
                (form.Donor_ID.data, form.Amount.data, form.Donation_date.data, form.Resource_ID.data, id))
            flash('Donation updated successfully', 'success')
            return redirect(url_for('donation_list'))
        except Exception as e:
            flash(str(e), 'danger')
    else:
        form.Donor_ID.data, form.Amount.data, form.Donation_date.data, form.Resource_ID.data = row[1], row[2], row[3], row[4]
    return render_template('form.html', form=form, title='Edit Donation')

@app.route('/donation/delete/<int:id>', methods=['POST'])
def donation_delete(id):
    try:
        execute_commit("DELETE FROM Donation WHERE Donation_ID=%s", (id,))
        flash('Donation deleted.', 'success')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('donation_list'))

@app.route('/disaster_delete_log')
def disaster_delete_log_list():
    rows = fetch_all("SELECT * FROM Disaster_Delete_Log ORDER BY Log_ID DESC")
    return render_template('disaster_delete_log.html', rows=rows)


if __name__ == '__main__':
    app.run(debug=True)
