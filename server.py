import os
import sys
import uuid
import subprocess
import psycopg2
import psycopg2.extras
from difflib import *
from werkzeug import secure_filename
from flask.ext.socketio import SocketIO, emit
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory

UPLOAD_FOLDER = 'static/user_files/'
INPUT_FOLDER = 'static/input_files/'
COMPARISON_FOLDER = 'static/comparison_files/'
ALLOWED_EXTENSIONS = set(['py'])
ALLOWED_INPUT_FILE_EXTENSIONS = set(['input'])
ALLOWED_COMP_FILE_EXTENSIONS = set(['cmp'])
reload(sys)
sys.setdefaultencoding("UTF8")
users = {}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['INPUT_FOLDER']  = INPUT_FOLDER
app.config['COMPARISON_FOLDER'] = COMPARISON_FOLDER
app.secret_key = os.urandom(24).encode('hex')
app.debug = True
socketio = SocketIO(app)


@socketio.on('connect', namespace='/checker')
def test_connect():
    print("connected")
    session['uuid']=uuid.uuid1()
    users[session['uuid']]={'username':'New User'}
    print("uuid: ", session['uuid'])
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    professors_query  = "SELECT title, last_name, user_info.id  FROM user_info join user_roles on user_info.id = user_roles.user_id JOIN roles on user_roles.role_id = roles.id"
    cur.execute(professors_query)
    professors = cur.fetchall()
    
    
    for professor in professors:
        print(professor)
        professor = {'title' : professor['title'], 'last_name' : professor['last_name'], 'id' : professor['id']}
        emit('load_professor', professor)

@socketio.on('uploadAssignmentt', namespace='/checker')
def uploadAssignment(assignment_id):
    users[session['uuid']]['assignment_id'] = assignment_id


@socketio.on('load_assignments', namespace='/checker')
def load_assignments(professor_id):
    # conn = connectToDB()
    # cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # assignments_query = """SELECT assignments.id, assignments.user_id, assignments.name, title, last_name  
    #                       FROM user_info join user_roles on user_info.id = user_roles.user_id 
    #                       JOIN assignments on user_info.id = assignments.user_id 
    #                       WHERE assignments.user_id = %s"""
    # cur.execute(assignments_query, (professor_id,))
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    assignments_query = "SELECT user_id, assignments.id as assignmentId, test_cases.id as testCaseId, input_file_path, comparison_file_path, name from assignments JOIN test_cases ON test_cases.assignment_id = assignments.id where user_id = %s" % professor_id
    cur.execute(assignments_query)
    assignments = cur.fetchall()
    for assignment in assignments:
        assignment = {'assignmentId': assignment[1], 'name' : assignment['name'], 'user_id': assignment['user_id'], 'testCaseId' : assignment[2], 'input_file_path' : assignment['input_file_path'].split('/')[2], 'comparison_file_path' : assignment['comparison_file_path'].split('/')[2]}
        emit('load_assignment', assignment)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
def allowed_input_file(filename):
    return '.' in filename and \
           filename.rsplit('.',1)[1] in ALLOWED_INPUT_FILE_EXTENSIONS
def allowed_comp_file(filename):
    return '.' in filename and \
           filename.rsplit('.',1)[1] in ALLOWED_COMP_FILE_EXTENSIONS
           
def connectToDB():
  connectionString = 'dbname=checker user=postgres password=postgres host=localhost'
  try:
    return psycopg2.connect(connectionString)
  except Exception as e:
    print(e)
    
@socketio.on('disconnect', namespace="/checker")
def on_disconnect():
    print("disconnecting")
    if session['uuid'] in users:
        del users[session['uuid']]

    
@socketio.on('load_administrators', namespace = '/checker')
def load_administrators():
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    load_administrators_query = "SELECT users.id, first_name, last_name, title, role from users JOIN user_info on users.id = user_info.id JOIN user_roles on users.id = user_roles.user_id JOIN roles on roles.id = user_roles.role_id"
    cur.execute(load_administrators_query)
    results = cur.fetchall()
    for result in results:
        result = {'firstname' : result['first_name'], 'lastname' : result['last_name'], 'title': result['title'], 'administratorId' : result['id'], 'role': result['role']}
        emit('load_administrator', result)
@socketio.on('validate_token', namespace="/checker")
def validate_token(token):
   
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    check_if_token_exists_query = "SELECT * from tokens where token = %s"
   
    cur.execute(check_if_token_exists_query, (token,))
    result = cur.fetchone()
    if result:
        if result[2] == False:
         
            consume_token_query = "UPDATE tokens SET consumed = true WHERE token = %s"
            cur.execute(consume_token_query, (token,))
            conn.commit()
            emit('valid_token')
        else:
           
            emit('invalid_token', 'This token has already been consumed')
    else: 
        emit('invalid_token', 'This is not a valid token')

@socketio.on('add_administrator', namespace = '/checker')
def add_administrator(administrator):
    
    if administrator['firstname'] == '' or administrator['lastname'] == '':
        pass
    elif administrator['title'] == '' or len(administrator['title']) > 3:
        pass
    elif administrator['role'] not in ['S-Administrator', 'Administrator']:
        pass
    else:    
        
        conn = connectToDB()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        
        add_admin_query = "INSERT INTO users VALUES ( default, %s, crypt(%s, gen_salt('bf')) ) RETURNING id"
        cur.execute(add_admin_query, (administrator['username'], administrator['password']))
        the_id = cur.fetchone()[0]
        add_admin_info_query = "INSERT INTO user_info values ( %s, %s, %s, %s )"
        cur.execute(add_admin_info_query, (the_id, administrator['firstname'], administrator['lastname'], administrator['title']))
        
        add_user_role_query = "INSERT INTO user_roles values ( %s, %s ) "
        cur.execute(add_user_role_query, (the_id, 2 if administrator['role'] == 'S-Administrator' else 1))
        conn.commit()
        emit('load_administrator', administrator)
    
@app.route('/add_assignment', methods=['POST'])
def addAssignment():
    assignmentName = request.form['assignmentName']
    try:
        input_file = request.files['input_file']
    except Exception as e:
        message.append("The following errors occurred:\n")
        message.append("- input file error")
        print e
    comp_file = None
    try:
        comp_file = request.files['comp_file']
    except Exception as e:
        if len(message) == 0:
            message.append("The following errors occurred:\n")
        message.append("- comp file error")
    
    if input_file and comp_file and len(assignmentName) > 0 and allowed_input_file(input_file.filename) and allowed_comp_file(comp_file.filename):
        conn = connectToDB()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        insert_assignment_query = "INSERT INTO assignments VALUES (default, %s, %s) RETURNING id"
        cur.execute(insert_assignment_query, (assignmentName , session['id'] ))
        assignmentId = cur.fetchone()[0]
    
        filename = secure_filename(input_file.filename)
        the_input_file_path = os.path.join(app.config['INPUT_FOLDER'], filename)
        input_file.save(the_input_file_path)
        filename = secure_filename(comp_file.filename)
        the_comp_file_path = os.path.join(app.config['COMPARISON_FOLDER'], filename)
        comp_file.save(the_comp_file_path)        
        
        insert_comp_file_query = "INSERT INTO test_cases VALUES (default, %s, %s, %s)"
        cur.execute(insert_comp_file_query, (the_input_file_path,the_comp_file_path, assignmentId))
            
        conn.commit()
    return redirect(url_for('admin_panel')) 
    
    
@app.route('/delete_assignment', methods=['POST'])    
def deleteAssignment():
    assignmentId = request.form['assignmentId']
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    delete_query = "DELETE FROM Assignments"
    
@socketio.on('update_administrator', namespace='/checker')
def update_administrator(administrator):
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    if administrator['firstname'] != "":
        update_first_name_query = "UPDATE user_info SET first_name = %s WHERE id = %s"
        cur.execute(update_first_name_query, (administrator['firstname'], administrator['administratorId']))
        conn.commit()
    if administrator['lastname'] != "":
        update_last_name_query = "UPDATE user_info SET last_name = %s WHERE id = %s"
        cur.execute(update_last_name_query, (administrator['lastname'], administrator['administratorId']))
        conn.commit()
    if administrator['title'] != "" and len(administrator['title']) < 4:
        update_title_query = "UPDATE user_info SET title = %s WHERE id = %s"
        cur.execute(update_title_query, (administrator['title'], administrator['administratorId']))
        conn.commit()
    if administrator['role'] == 'S-Administrator':
        update_role_query = "UPDATE user_roles SET role_id = %s WHERE user_id = %s"
        cur.execute(update_role_query, (2, administrator['administratorId']))
        conn.commit()
    elif administrator['role'] == 'Administrator':
        update_role_query = "UPDATE user_roles SET role_id = %s WHERE user_id = %s"
        cur.execute(update_role_query, (1, administrator['administratorId']))
        conn.commit()
        

@app.route('/edit_assignment', methods=['POST'])
def editAssignment():
    assignmentId = request.form['assignmentId']
    assignmentName = request.form['assignmentName']
    input_file,comp_file = None,None
    
    message = []
    input_file = None
    try:
        input_file = request.files['input_file']
    except Exception as e:
        message.append("The following errors occurred:\n")
        message.append("- input file error")
        print e
    comp_file = None
    try:
        comp_file = request.files['comp_file']
    except Exception as e:
        if len(message) == 0:
            message.append("The following errors occurred:\n")
        message.append("- comp file error")
    
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if len(assignmentName) > 0:
        update_assignment_name_query = "UPDATE assignments SET name= %s WHERE id= %s"
        cur.execute(update_assignment_name_query, (assignmentName, assignmentId))
        conn.commit()
    if input_file and allowed_input_file(input_file.filename):
        filename = secure_filename(input_file.filename)
        the_input_file_path = os.path.join(app.config['INPUT_FOLDER'], filename)
        input_file.save(the_input_file_path)
        insert_input_file_query = "UPDATE test_cases SET input_file_path= %s WHERE assignment_id= %s"
        cur.execute(insert_input_file_query, (the_input_file_path, assignmentId))
        conn.commit()
        
    if comp_file and allowed_comp_file(comp_file.filename):
        filename = secure_filename(comp_file.filename)
        the_comp_file_path = os.path.join(app.config['COMPARISON_FOLDER'], filename)
        comp_file.save(the_comp_file_path)
        insert_comp_file_query = "UPDATE test_cases SET comparison_file_path= %s WHERE assignment_id= %s"
        cur.execute(insert_comp_file_query, (the_comp_file_path, assignmentId))
        conn.commit()
    
    print('assignmentId: ' + assignmentId)
    print('assignmentName: ' + assignmentName)
    print('input_file: ' + str(input_file))
    print('comp_file: ' + str(comp_file))
    
    print("".join(message))
    return redirect(url_for('admin_panel'))
    
@app.route('/upload_file', methods=['POST'])
def upload_file():
     
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        userfile = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        outfile = os.path.join(app.config['UPLOAD_FOLDER'], filename[:-2] + 'out')
        
        
        assignment_id = request.form['assignment_id']
        
        conn = connectToDB()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        test_case_query = """SELECT input_file_path, comparison_file_path from test_cases WHERE assignment_id = %s"""
        assignment_id = request.form['assignment_id']
        print('assignment_id: ', assignment_id)
        cur.execute(test_case_query, (assignment_id,))
        result = cur.fetchone()
        
        if not result: # ERROR - No Test Case Found
            print("no test case found")
            return redirect(url_for('index'))
            
        file.save(userfile)
        infile = result['input_file_path']
        
        # pipe input into python
        infile_shell = "echo \"$(cat %s)\" | python " % infile
        shell_command =  infile_shell + userfile + " > " + outfile 
        
        os.system(shell_command)
        
        #diff_command = "diff %s %s" % result[0], outfile
        #os.system(diff_command)
        
        compare_file = open(result['comparison_file_path'])
        compare_lines = compare_file.readlines()
        output_file = open(outfile)
        output_lines = output_file.readlines()
        
        d = Differ()
        results = list(d.compare(compare_lines, output_lines))
        print("compare_file: " , compare_lines)
        print("output_file: " , output_lines)
        print("difference: ", results)
        token = ""
        get_token = True
        message_text = []
        message_text.append("The output of the file you submitted did not match the test-cases.")
        for result in results:
            print("first char: " , result[0])
            if result[0] == ' ':
                # output matches comparison text
                pass
            elif result[0] == '-': # missing
                # message_text.append('Missing: ' + str(result))
                get_token = False 
                
            elif result[0] == '+': # added
                # message_text.append('Extra: ' + str(result))
                get_token = False
                
            elif result[0] == '?': # 
                # message_text.append('Wtf: ' + str(result))
                get_token = False
        
        if get_token:
            message = "success"
            token = os.urandom(10).encode('hex')
            insert_token_query = "INSERT INTO tokens VALUES ( default, %s, false)"
            cur.execute(insert_token_query, (token,))
            conn.commit()
            message_text = []
            message_text.append("Congratulations! Your code passed the test cases! Here is your token: %s" % token )
            #token =
        else:
            message = "error"
            
            
        # TODO
        # delete files uploaded by user
        
        return render_template("index.html", message = message, token=token, open_squiggle = "{{", close_squiggle = "}}", message_text = message_text, student_lines = output_lines, professor_lines = compare_lines); 
        
    return redirect(url_for("index"))
 

        
    
@app.route('/', methods=["POST","GET"])
def index():
    # assignment = {'title': 'dummy', 
    # professor = {'title': 'dummy', 'last_name' : 'dummy', 'id' : 'dummy'}
   
    return render_template('index.html', open_squiggle = "{{", close_squiggle = "}}")
    
@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    if 'Administrator' in session or 'S-Administrator' in session:
        conn = connectToDB()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        assignments_query = "SELECT user_id, assignments.id as assignmentsId, test_cases.id as testCasesId, input_file_path, comparison_file_path, name from assignments JOIN test_cases ON test_cases.assignment_id = assignments.id where user_id = %s" % session['id']
        cur.execute(assignments_query)
        results = cur.fetchall()
        print('assignments: ')
        print(results)
        conn = connectToDB()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        professors_query  = "SELECT *  FROM user_info WHERE id = %s"
        cur.execute(professors_query, (session['id'],))
        professor = cur.fetchone()
        #emit('clear_assignments', 'garbage')
        # for assignment in results:
        #     emit('load_assignment', {'id': assignment['id'], 'name' : assignment['name'], 'user_id': assignment['user_id']})
        
        return render_template('admin_panel.html', assignments=results,open_squiggle = "{{", close_squiggle = "}}", professor = professor )    
    
    return redirect(url_for('login'))
    
@app.route('/results', methods=['GET'])
def results_page(filename):
    #do processing
    return render_template('results.html', filename)
    
@app.route('/help', methods=['GET'])
def help():
    return render_template('help.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connectToDB()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        login_query = "SELECT * FROM users WHERE username = %s AND password = crypt(%s, password)"
        cur.execute(login_query, (username, password))
        result = cur.fetchone()
        if result:
            role_query = "SELECT role FROM user_roles JOIN roles ON user_roles.role_id = roles.id WHERE user_id = %s" % result['id']
            cur.execute(role_query)
            role = cur.fetchone()['role']

            session['username'] = username
            session['id'] = result['id']
            
            if role == 'Administrator':
                session['Administrator'] = True
            elif role == 'S-Administrator':
                session['S-Administrator'] = True
            return redirect(url_for('admin_panel'))
        return render_template('login.html', user_not_found=True)
    return render_template('login.html')
    
@app.route('/about', methods=['POST', 'GET'])
def about():
    return render_template('about.html')
@app.route('/register', methods=['POST', 'GET'])
def register():
    return render_template('register.html')
    
@app.route('/logout')
def logout():
    for key, value in session.items():
        session.pop(key, None)
    return redirect(url_for('index'))
        
if __name__ == '__main__':
    app.debug=True
    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
    #app.run(host='0.0.0.0', port=8080)
