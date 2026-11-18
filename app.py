"""CampusOne Flask API and static application server."""
import os, json, sqlite3, secrets, re, logging
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, g, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
DATA=Path(os.environ.get('CAMPUSONE_DATA_DIR',ROOT/'instance')); DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'campusone.sqlite3'; UPLOADS=DATA/'uploads'; UPLOADS.mkdir(exist_ok=True)
app=Flask(__name__, static_folder='frontend', static_url_path='')
app.config.update(SECRET_KEY=os.environ.get('CAMPUSONE_SECRET') or 'dev-only-change-this-secret', MAX_CONTENT_LENGTH=5*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0')=='1')
logging.basicConfig(level=os.environ.get('LOG_LEVEL','INFO'))
MODULES={'teams':'projects','tutoring':'tutors','lost-found':'items','opportunities':'opportunities'}
ALLOWED_UPLOAD={'png','jpg','jpeg','webp'}

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def db():
    if 'db' not in g:
        g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row; g.db.execute('PRAGMA foreign_keys=ON'); g.db.execute('PRAGMA busy_timeout=5000')
    return g.db
@app.teardown_appcontext
def close_db(_=None):
    conn=g.pop('db',None)
    if conn: conn.close()
def init_db():
    c=sqlite3.connect(DB); c.executescript('''
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','admin')), active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, department TEXT DEFAULT '', year TEXT DEFAULT '', skills TEXT DEFAULT '[]', interests TEXT DEFAULT '[]', experience TEXT DEFAULT '', availability TEXT DEFAULT '', bio TEXT DEFAULT '', updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, module TEXT NOT NULL, kind TEXT NOT NULL, owner_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, data TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'Open', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_records_module_kind ON records(module,kind,status,created_at);
    CREATE INDEX IF NOT EXISTS idx_records_owner ON records(owner_id,module);
    CREATE TABLE IF NOT EXISTS links(id INTEGER PRIMARY KEY, record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE, sender_id INTEGER NOT NULL REFERENCES users(id), recipient_id INTEGER NOT NULL REFERENCES users(id), kind TEXT NOT NULL, message TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Pending', data TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(record_id,sender_id,kind));
    CREATE INDEX IF NOT EXISTS idx_links_recipient ON links(recipient_id,status);
    CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, title TEXT NOT NULL, message TEXT NOT NULL, url TEXT DEFAULT '', read INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE, actor_id INTEGER NOT NULL REFERENCES users(id), status TEXT NOT NULL, note TEXT DEFAULT '', created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS bookmarks(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE, created_at TEXT NOT NULL, PRIMARY KEY(user_id,record_id));
    CREATE TABLE IF NOT EXISTS team_members(id INTEGER PRIMARY KEY, team_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, invited_by INTEGER NOT NULL REFERENCES users(id), role TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Accepted','Declined','Left')), created_at TEXT NOT NULL, updated_at TEXT NOT NULL, UNIQUE(team_id,user_id));
    CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id,status);
    CREATE TABLE IF NOT EXISTS password_resets(email TEXT PRIMARY KEY, token_hash TEXT NOT NULL, expires_at TEXT NOT NULL);
    '''); c.commit();
    admin=os.environ.get('CAMPUSONE_ADMIN_EMAIL','').lower()
    if admin: c.execute("UPDATE users SET role='admin' WHERE email=?",(admin,)); c.commit()
    c.close()
init_db()

def user():
    uid=session.get('uid')
    return db().execute('SELECT id,name,email,role FROM users WHERE id=? AND active=1',(uid,)).fetchone() if uid else None
def login_required(fn):
    @wraps(fn)
    def inner(*a,**kw):
        if not user(): return jsonify(error='Sign in to continue.'),401
        return fn(*a,**kw)
    return inner
def admin_required(fn):
    @wraps(fn)
    def inner(*a,**kw):
        u=user()
        if not u: return jsonify(error='Sign in to continue.'),401
        if u['role']!='admin': return jsonify(error='Administrator access required.'),403
        return fn(*a,**kw)
    return inner
def payload(): return request.get_json(silent=True) or {}
def notify(uid,title,message,url=''):
    if uid: db().execute('INSERT INTO notifications(user_id,title,message,url,created_at) VALUES(?,?,?,?,?)',(uid,title,message,url,now()))
def record_dict(row,include_owner=False):
    d=dict(row); d['data']=json.loads(d['data'] or '{}')
    if include_owner: d['owner']=dict(db().execute('SELECT id,name,email FROM users WHERE id=?',(d.pop('owner_id'),)).fetchone())
    return d
def api_error(msg,status=400): return jsonify(error=msg),status

@app.get('/api/health')
def health(): return jsonify(status='ok',app='CampusOne',database='sqlite3')
@app.post('/api/auth/register')
def register():
    d=payload(); name=str(d.get('name','')).strip(); email=str(d.get('email','')).strip().lower(); pw=str(d.get('password','')); confirm=str(d.get('confirm_password',pw))
    if len(name)<2 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email): return api_error('Enter your name and a valid email address.')
    if len(pw)<10 or pw!=confirm: return api_error('Use a matching password with at least 10 characters.')
    try:
        c=db(); role='admin' if email==os.environ.get('CAMPUSONE_ADMIN_EMAIL','').strip().lower() else 'student'; cur=c.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',(name,email,generate_password_hash(pw),role,now())); uid=cur.lastrowid
        c.execute('INSERT INTO profiles(user_id,updated_at) VALUES(?,?)',(uid,now())); c.commit(); session.clear(); session['uid']=uid
        return jsonify(user=dict(id=uid,name=name,email=email,role=role)),201
    except sqlite3.IntegrityError: return api_error('An account already uses that email.',409)
@app.post('/api/auth/login')
def auth_login():
    d=payload(); email=str(d.get('email','')).strip().lower(); row=db().execute('SELECT * FROM users WHERE email=? AND active=1',(email,)).fetchone()
    if not row or not check_password_hash(row['password_hash'],str(d.get('password',''))): return api_error('Email or password is incorrect.',401)
    session.clear(); session['uid']=row['id']; return jsonify(user={k:row[k] for k in ('id','name','email','role')})
@app.post('/api/auth/logout')
def auth_logout(): session.clear(); return jsonify(ok=True)
@app.get('/api/auth/me')
@login_required
def auth_me():
    u=user(); p=db().execute('SELECT * FROM profiles WHERE user_id=?',(u['id'],)).fetchone(); return jsonify(user=dict(u),profile=dict(p) if p else {})
@app.post('/api/auth/forgot-password')
def forgot():
    # Safe by default: deployment may wire an email provider; never disclose account existence.
    d=payload(); email=str(d.get('email','')).lower().strip(); row=db().execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()
    if row and app.config['SECRET_KEY']!='dev-only-change-this-secret':
        token=secrets.token_urlsafe(32); db().execute('INSERT OR REPLACE INTO password_resets VALUES(?,?,?)',(email,generate_password_hash(token),now())); db().commit(); app.logger.info('Password reset requested; configure a mail provider to deliver token.')
    return jsonify(message='If the account exists, password reset instructions will be sent when email delivery is configured.')
@app.route('/api/profile',methods=['GET','PUT'])
@login_required
def profile():
    u=user(); c=db()
    if request.method=='GET':
        p=c.execute('SELECT * FROM profiles WHERE user_id=?',(u['id'],)).fetchone(); return jsonify(profile=dict(p))
    d=payload(); fields={k:d.get(k) for k in ('department','year','experience','availability','bio') if k in d}
    for k in ('skills','interests'):
        if k in d:
            value=d[k]; value=[x.strip() for x in value.split(',')] if isinstance(value,str) else value
            fields[k]=json.dumps([str(x)[:80] for x in value if str(x).strip()][:40])
    sets=','.join(f'{k}=?' for k in fields); vals=list(fields.values())
    if sets: c.execute(f'UPDATE profiles SET {sets},updated_at=? WHERE user_id=?',(*vals,now(),u['id'])); c.commit()
    p=c.execute('SELECT * FROM profiles WHERE user_id=?',(u['id'],)).fetchone(); return jsonify(profile=dict(p))

@app.get('/api/students')
@login_required
def find_students():
    q=request.args.get('q','').strip().casefold(); department=request.args.get('department','').strip().casefold(); c=db()
    rows=c.execute("SELECT u.id,u.name,p.department,p.year,p.skills,p.interests,p.availability,p.bio FROM users u JOIN profiles p ON p.user_id=u.id WHERE u.active=1 AND u.role='student' AND u.id!=? ORDER BY u.name LIMIT 200",(user()['id'],)).fetchall()
    results=[]
    for r in rows:
        x=dict(r); skills=json.loads(x.pop('skills') or '[]'); interests=json.loads(x.pop('interests') or '[]'); hay=' '.join([x['name'],x['department'],x['year'],x['availability'],x['bio'],' '.join(skills),' '.join(interests)]).casefold()
        if (not q or q in hay) and (not department or department in x['department'].casefold()):
            x['skills']=skills; x['interests']=interests; results.append(x)
    return jsonify(students=results[:80])

@app.post('/api/teams/<int:team_id>/invitations')
@login_required
def invite_team_member(team_id):
    d=payload(); c=db(); team=c.execute("SELECT * FROM records WHERE id=? AND module='teams'",(team_id,)).fetchone(); uid=d.get('user_id')
    if not team: return api_error('Team not found.',404)
    if team['owner_id']!=user()['id']: return api_error('Only the team owner can invite members.',403)
    try: uid=int(uid)
    except (TypeError,ValueError): return api_error('Choose a student to invite.')
    student=c.execute("SELECT id,name FROM users WHERE id=? AND role='student' AND active=1",(uid,)).fetchone()
    if not student: return api_error('Student account not found.',404)
    if uid==user()['id']: return api_error('You are already the team owner.')
    try:
        cur=c.execute('INSERT INTO team_members(team_id,user_id,invited_by,role,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(team_id,uid,user()['id'],str(d.get('role',''))[:100],'Pending',now(),now()))
    except sqlite3.IntegrityError: return api_error('This student already has a team invitation or membership.',409)
    notify(uid,'Team invitation',user()['name']+' invited you to join “'+team['title']+'”.','/requests'); c.commit()
    return jsonify(invitation_id=cur.lastrowid,status='Pending',student=student['name']),201

@app.get('/api/teams/<int:team_id>/members')
@login_required
def team_roster(team_id):
    c=db(); team=c.execute("SELECT * FROM records WHERE id=? AND module='teams'",(team_id,)).fetchone()
    if not team: return api_error('Team not found.',404)
    if team['owner_id']!=user()['id'] and not c.execute("SELECT 1 FROM team_members WHERE team_id=? AND user_id=? AND status='Accepted'",(team_id,user()['id'])).fetchone(): return api_error('Team membership required.',403)
    members=c.execute('SELECT tm.id,tm.user_id,tm.role,tm.status,tm.created_at,u.name,p.department,p.year FROM team_members tm JOIN users u ON u.id=tm.user_id JOIN profiles p ON p.user_id=u.id WHERE tm.team_id=? ORDER BY tm.created_at',(team_id,)).fetchall()
    owner=c.execute('SELECT u.id,u.name,p.department,p.year FROM users u JOIN profiles p ON p.user_id=u.id WHERE u.id=?',(team['owner_id'],)).fetchone()
    return jsonify(owner=dict(owner),members=[dict(m) for m in members])

@app.put('/api/teams/invitations/<int:invitation_id>')
@login_required
def answer_team_invitation(invitation_id):
    d=payload(); status=d.get('status'); c=db(); row=c.execute('SELECT tm.*,r.title FROM team_members tm JOIN records r ON r.id=tm.team_id WHERE tm.id=?',(invitation_id,)).fetchone()
    if not row: return api_error('Invitation not found.',404)
    if row['user_id']!=user()['id']: return api_error('This invitation belongs to another student.',403)
    if row['status']!='Pending': return api_error('This invitation has already been answered.',409)
    if status not in ('Accepted','Declined'): return api_error('Choose accept or decline.')
    c.execute('UPDATE team_members SET status=?,updated_at=? WHERE id=?',(status,now(),invitation_id)); notify(row['invited_by'],'Team invitation '+status.lower(),user()['name']+' '+status.lower()+' your invitation to “'+row['title']+'”.','/teams'); c.commit()
    return jsonify(ok=True,status=status)

def module_records(module):
    if module not in MODULES: return None
    c=db(); rows=c.execute('SELECT r.*,u.name owner_name FROM records r JOIN users u ON u.id=r.owner_id WHERE r.module=? AND r.kind=? ORDER BY r.created_at DESC LIMIT 200',(module,MODULES[module])).fetchall()
    out=[]
    for row in rows:
        item=record_dict(row); item['owner']={'id':row['owner_id'],'name':row['owner_name']}; item['is_owner']=row['owner_id']==user()['id']; item['bookmarked']=bool(c.execute('SELECT 1 FROM bookmarks WHERE user_id=? AND record_id=?',(user()['id'],row['id'])).fetchone()); out.append(item)
    return out
@app.get('/api/<module>')
@login_required
def list_records(module):
    items=module_records(module)
    if items is None: return api_error('Unknown module.',404)
    q=request.args.get('q','').strip().casefold(); cat=request.args.get('category','').casefold(); dept=request.args.get('department','').casefold(); status=request.args.get('status','').casefold()
    items=[r for r in items if (not q or q in (r['title']+' '+json.dumps(r['data'])).casefold()) and (not cat or cat in str(r['data'].get('category','')).casefold() or cat in str(r['data'].get('subject','')).casefold()) and (not dept or dept in str(r['data'].get('department','')).casefold()) and (not status or status==r['status'].casefold())]
    if request.args.get('mine')=='1': items=[x for x in items if x['is_owner']]
    if module=='opportunities' and request.args.get('saved')=='1': items=[x for x in items if x['bookmarked']]
    if module=='teams' and request.args.get('match')=='1':
        p=db().execute('SELECT skills,interests,availability FROM profiles WHERE user_id=?',(user()['id'],)).fetchone(); skills=set(json.loads(p['skills'] or '[]')); interests=set(json.loads(p['interests'] or '[]'))
        for x in items:
            req=set(x['data'].get('required_skills',[])); x['match_score']=round(100*(len(req&skills)/max(1,len(req))*.8 + bool(set(x['data'].get('interests',[]))&interests)*.15 + bool(p['availability'] and p['availability'] in x['data'].get('availability',''))*.05))
        items.sort(key=lambda x:x.get('match_score',0),reverse=True)
    return jsonify(items=items)
@app.post('/api/<module>')
@login_required
def create_record(module):
    if module not in MODULES: return api_error('Unknown module.',404)
    if module=='opportunities' and user()['role']!='admin': return api_error('Only administrators can publish opportunities.',403)
    d=payload(); title=str(d.get('title','')).strip(); data=d.get('data',{})
    if not title or len(title)>180 or not isinstance(data,dict): return api_error('A title and valid details are required.')
    if module=='issues': data['complaint_id']=data.get('complaint_id') or 'CO-'+secrets.token_hex(4).upper()
    status='Submitted' if module=='issues' else ('Pending' if module in ('tutoring','mentors') else 'Open')
    c=db(); cur=c.execute('INSERT INTO records(module,kind,owner_id,title,data,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(module,MODULES[module],user()['id'],title,json.dumps(data),status,now(),now())); rid=cur.lastrowid
    c.execute('INSERT INTO history(record_id,actor_id,status,note,created_at) VALUES(?,?,?,?,?)',(rid,user()['id'],status,'Created',now()))
    if module=='opportunities':
        for r in c.execute("SELECT id FROM users WHERE role='student' AND id!=?",(user()['id'],)).fetchall(): notify(r['id'],'New campus opportunity',title,'/opportunities')
    c.commit(); return jsonify(item=record_dict(c.execute('SELECT * FROM records WHERE id=?',(rid,)).fetchone())),201
@app.post('/api/<module>/<int:rid>/requests')
@login_required
def request_record(module,rid):
    if module not in MODULES: return api_error('Unknown module.',404)
    c=db(); rec=c.execute('SELECT * FROM records WHERE id=? AND module=?',(rid,module)).fetchone()
    if not rec: return api_error('Listing not found.',404)
    if rec['owner_id']==user()['id']: return api_error('You cannot request your own listing.')
    d=payload(); kind={'teams':'team_invite','tutoring':'tutoring_session','lost-found':'item_claim','mentors':'mentor_request','issues':'issue_followup','opportunities':'opportunity_question'}[module]
    try:
        cur=c.execute('INSERT INTO links(record_id,sender_id,recipient_id,kind,message,data,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(rid,user()['id'],rec['owner_id'],kind,str(d.get('message',''))[:1000],json.dumps(d),now(),now()))
    except sqlite3.IntegrityError: return api_error('You already sent a request for this listing.',409)
    notify(rec['owner_id'],'New '+kind.replace('_',' '),user()['name']+' sent a request about “'+rec['title']+'”.','/notifications'); c.commit(); return jsonify(request_id=cur.lastrowid,status='Pending'),201
@app.get('/api/requests')
@login_required
def requests_list():
    c=db(); rows=c.execute('SELECT l.*,r.title,u.name sender_name,u2.name recipient_name FROM links l JOIN records r ON r.id=l.record_id JOIN users u ON u.id=l.sender_id JOIN users u2 ON u2.id=l.recipient_id WHERE l.sender_id=? OR l.recipient_id=? ORDER BY l.created_at DESC',(user()['id'],user()['id'])).fetchall()
    result=[dict(x) for x in rows]
    invites=c.execute('SELECT tm.id,tm.team_id,tm.user_id,tm.invited_by,tm.role,tm.status,tm.created_at,r.title,u.name inviter_name,u2.name invitee_name FROM team_members tm JOIN records r ON r.id=tm.team_id JOIN users u ON u.id=tm.invited_by JOIN users u2 ON u2.id=tm.user_id WHERE tm.user_id=? OR tm.invited_by=? ORDER BY tm.created_at DESC',(user()['id'],user()['id'])).fetchall()
    for x in invites:
        i=dict(x); i.update(kind='team_invitation',message=i['role'],sender_id=i['invited_by'],recipient_id=i['user_id'],sender_name=i['inviter_name'],recipient_name=i['invitee_name'],is_team_invitation=True); result.append(i)
    result.sort(key=lambda x:x['created_at'],reverse=True)
    return jsonify(requests=result)
@app.put('/api/requests/<int:lid>')
@login_required
def update_request(lid):
    d=payload(); status=d.get('status'); c=db(); row=c.execute('SELECT * FROM links WHERE id=?',(lid,)).fetchone()
    if not row: return api_error('Request not found.',404)
    if row['recipient_id']!=user()['id'] and user()['role']!='admin': return api_error('Only the recipient can respond.',403)
    if status not in ('Confirmed','Declined','Cancelled','Completed','Alternative suggested','Returned','Rejected'): return api_error('Invalid request status.')
    c.execute('UPDATE links SET status=?,updated_at=? WHERE id=?',(status,now(),lid)); notify(row['sender_id'],'Request '+status.lower(),'Your request is now '+status.lower()+'.','/notifications')
    if status in ('Confirmed','Returned'): c.execute('UPDATE records SET status=?,updated_at=? WHERE id=?',('Claim Pending' if row['kind']=='item_claim' and status=='Confirmed' else status,now(),row['record_id']))
    c.commit(); return jsonify(ok=True,status=status)
@app.post('/api/<module>/<int:rid>/bookmark')
@login_required
def bookmark(module,rid):
    if module!='opportunities': return api_error('Bookmarks are supported for opportunities only.',404)
    c=db(); exists=c.execute('SELECT 1 FROM bookmarks WHERE user_id=? AND record_id=?',(user()['id'],rid)).fetchone()
    if exists: c.execute('DELETE FROM bookmarks WHERE user_id=? AND record_id=?',(user()['id'],rid)); saved=False
    else:
        if not c.execute('SELECT 1 FROM records WHERE id=? AND module=?',(rid,module)).fetchone(): return api_error('Opportunity not found.',404)
        c.execute('INSERT INTO bookmarks VALUES(?,?,?)',(user()['id'],rid,now())); saved=True
    c.commit(); return jsonify(saved=saved)
@app.post('/api/upload')
@login_required
def upload():
    f=request.files.get('file')
    if not f or not f.filename: return api_error('Choose an image to upload.')
    name=secure_filename(f.filename); ext=name.rsplit('.',1)[-1].lower() if '.' in name else ''
    if ext not in ALLOWED_UPLOAD or not (f.mimetype or '').startswith('image/'): return api_error('Upload a PNG, JPG or WEBP image.')
    fname=secrets.token_hex(16)+'.'+ext; f.save(UPLOADS/fname); return jsonify(url='/uploads/'+fname),201
@app.get('/uploads/<path:name>')
@login_required
def uploaded(name): return send_from_directory(UPLOADS,name,as_attachment=False)
@app.get('/api/notifications')
@login_required
def notifications():
    rows=db().execute('SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 100',(user()['id'],)).fetchall(); return jsonify(notifications=[dict(r) for r in rows])
@app.put('/api/notifications/<int:nid>/read')
@login_required
def notification_read(nid):
    c=db(); cur=c.execute('UPDATE notifications SET read=1 WHERE id=? AND user_id=?',(nid,user()['id'])); c.commit(); return jsonify(ok=bool(cur.rowcount))
@app.get('/api/dashboard')
@login_required
def dashboard():
    c=db(); uid=user()['id']; stats={}
    for mod in MODULES: stats[mod]=c.execute('SELECT count(*) FROM records WHERE module=? AND (owner_id=? OR module=?)',(mod,uid,mod)).fetchone()[0]
    incoming=c.execute("SELECT count(*) FROM links WHERE recipient_id=? AND status='Pending'",(uid,)).fetchone()[0]; unread=c.execute('SELECT count(*) FROM notifications WHERE user_id=? AND read=0',(uid,)).fetchone()[0]
    recent=c.execute('SELECT id,module,title,status,created_at FROM records WHERE owner_id=? ORDER BY created_at DESC LIMIT 5',(uid,)).fetchall()
    return jsonify(stats=stats,pending_requests=incoming,unread_notifications=unread,recent=[dict(x) for x in recent])
@app.get('/api/admin/dashboard')
@admin_required
def admin_dashboard():
    c=db(); stats={'students':c.execute("SELECT count(*) FROM users WHERE role='student'").fetchone()[0], 'active_users':c.execute("SELECT count(*) FROM users WHERE active=1").fetchone()[0]}
    for m in MODULES: stats[m]=c.execute('SELECT count(*) FROM records WHERE module=?',(m,)).fetchone()[0]
    return jsonify(stats=stats,users=[dict(x) for x in c.execute('SELECT id,name,email,role,active,created_at FROM users ORDER BY created_at DESC LIMIT 100')])
@app.put('/api/admin/users/<int:uid>')
@admin_required
def admin_user(uid):
    d=payload(); active=1 if d.get('active') else 0; c=db(); cur=c.execute('UPDATE users SET active=? WHERE id=? AND role!=\'admin\'',(active,uid)); c.commit(); return jsonify(ok=bool(cur.rowcount))
@app.put('/api/admin/records/<int:rid>')
@admin_required
def admin_record(rid):
    d=payload(); status=str(d.get('status','')).strip(); allowed={'lost-found':{'Open','Claim Pending','Returned','Closed'}}
    c=db(); r=c.execute('SELECT * FROM records WHERE id=?',(rid,)).fetchone()
    if not r: return api_error('Record not found.',404)
    if status not in allowed.get(r['module'],set()): return api_error('Invalid status for this record.')
    c.execute('UPDATE records SET status=?,updated_at=? WHERE id=?',(status,now(),rid)); c.execute('INSERT INTO history(record_id,actor_id,status,note,created_at) VALUES(?,?,?,?,?)',(rid,user()['id'],status,str(d.get('note',''))[:1000],now())); notify(r['owner_id'],'Update: '+r['title'],'Status changed to '+status+'. '+str(d.get('note','')),'/issues'); c.commit(); return jsonify(ok=True)
@app.get('/api/records/<int:rid>/history')
@login_required
def record_history(rid):
    c=db(); r=c.execute('SELECT owner_id FROM records WHERE id=?',(rid,)).fetchone()
    if not r: return api_error('Record not found.',404)
    if r['owner_id']!=user()['id'] and user()['role']!='admin': return api_error('Access denied.',403)
    return jsonify(history=[dict(x) for x in c.execute('SELECT h.*,u.name actor FROM history h JOIN users u ON u.id=h.actor_id WHERE record_id=? ORDER BY h.created_at',(rid,))])
@app.errorhandler(413)
def too_large(_): return jsonify(error='Image exceeds the 5 MB limit.'),413
@app.errorhandler(500)
def internal(_): app.logger.exception('Unhandled request error'); return jsonify(error='The server could not complete this request.'),500
@app.get('/')
def index(): return send_from_directory('frontend','index.html')
if __name__=='__main__': app.run(host=os.environ.get('HOST','127.0.0.1'),port=int(os.environ.get('PORT','5000')),debug=os.environ.get('FLASK_DEBUG')=='1')
