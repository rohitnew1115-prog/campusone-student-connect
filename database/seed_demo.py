"""Add clearly labelled, fictional showcase content to the local CampusOne DB.

Run: python database/seed_demo.py
Safe to rerun; records and member invitations are de-duplicated by title/email.
"""
import secrets
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as campus

PEOPLE=[
 ('Anika Menon','Computing','Year 3',['Python','Flask','SQL'],['Open source','Accessibility'],'Weekday evenings','Builds accessible campus tools.'),
 ('Ishan Kapoor','Design','Year 2',['Figma','UI design','CSS'],['Product design','Photography'],'Weekends','Enjoys turning complex ideas into simple interfaces.'),
 ('Meera Nair','Electronics','Year 4',['Arduino','IoT','C++'],['Robotics','Sustainability'],'Tue/Thu afternoons','Works on low-cost campus energy monitors.'),
 ('Dev Shah','Computing','Year 2',['JavaScript','Node','Python'],['Web apps','Hackathons'],'Weekday evenings','Full-stack learner who likes rapid prototypes.'),
 ('Tara Iyer','Biotechnology','Year 3',['Research','Data analysis','Python'],['Health','Climate'],'Mon/Wed mornings','Interested in data-led student research.'),
 ('Arjun Rao','Mechanical','Year 4',['CAD','3D printing','Prototyping'],['Robotics','Mobility'],'Friday afternoons','Builds and tests physical prototypes.'),
 ('Nisha Das','Computing','Year 1',['Java','HTML','Writing'],['Cybersecurity','Games'],'After 4 pm','First-year student eager to learn by building.'),
 ('Kavya Joseph','Business','Year 3',['Research','Presentation','Excel'],['Entrepreneurship','Impact'],'Weekends','Helps teams with research, planning and pitches.'),
 ('Rohan Bose','Physics','Year 2',['Python','Statistics','Lab work'],['Astronomy','AI'],'Flexible','Peer tutor for introductory quantitative subjects.'),
 ('Sara Thomas','Civil','Year 4',['GIS','AutoCAD','Surveying'],['Water','Urban design'],'Wed/Fri','Interested in accessible and sustainable campus spaces.'),
]

PROJECTS=[
 ('Campus event finder','A lightweight calendar that gathers talks, clubs and workshops in one searchable place.',['JavaScript','UI design','Flask'],4,'Product design','Weekday evenings'),
 ('Smart lab energy monitor','Prototype low-cost sensors to help teaching labs spot wasted electricity.',['Arduino','IoT','Data analysis'],5,'Sustainability','Tue/Thu afternoons'),
 ('Accessible route mapper','Map step-free routes between teaching blocks and flag temporary barriers.',['GIS','Accessibility','Web apps'],4,'Campus access','Weekends'),
 ('Peer study room matcher','Coordinate quiet study groups by subject, pace and availability.',['Python','Database design','UI design'],4,'Student learning','After 4 pm'),
 ('Campus pantry inventory','Help student volunteers track pantry stock and reduce food waste.',['Web apps','Research','UI design'],5,'Community','Flexible'),
 ('Low-cost weather station','Collect local temperature, humidity and rainfall readings for class projects.',['Arduino','C++','Data analysis'],4,'Climate','Weekday evenings'),
 ('First-year coding buddy','A friendly set of guided exercises and peer support for programming basics.',['Java','Writing','Accessibility'],3,'Peer learning','Weekends'),
 ('Campus recycling guide','Identify sorting rules and collection points with clear visuals for students.',['Figma','Photography','Research'],3,'Sustainability','Flexible'),
]

TUTORS=[
 ('Python foundations with Rohan','Python','Variables, loops and beginner projects','Rohan Bose'),('Calculus study sessions','Calculus','Limits, derivatives and practice problems','Meera Nair'),
 ('Java programming peer help','Java','Classes, arrays and debugging','Nisha Das'),('Statistics for research','Statistics','Descriptive statistics and charts','Tara Iyer'),
 ('Introductory electronics lab','Electronics','Circuit basics and Arduino','Meera Nair'),('Academic writing studio','Writing','Structure, clarity and citations','Kavya Joseph'),
 ('CAD and design review','CAD','Sketches, assemblies and print prep','Arjun Rao'),('GIS mapping basics','GIS','Layers, coordinates and map design','Sara Thomas'),
]
MENTORS=[
 ('Finding your footing in Year 1','Computing','Year 3',['Study planning','Campus life'],'Weekday evenings'),('Getting started with research','Biotechnology','Year 4',['Research','Lab skills'],'Mon/Wed'),
 ('Portfolio feedback for designers','Design','Year 4',['UI design','Figma'],'Weekends'),('Robotics project mentoring','Electronics','Year 4',['Arduino','Prototyping'],'Tue/Thu'),
 ('Internship search and interview prep','Business','Year 4',['Career planning','Presentations'],'Friday afternoons'),('Making your first web app','Computing','Year 3',['JavaScript','Flask'],'After 4 pm'),
 ('Engineering project planning','Mechanical','Year 4',['CAD','Prototyping'],'Flexible'),('Campus volunteering guide','Civil','Year 4',['Community','Sustainability'],'Weekends'),
]
OPPORTUNITIES=[
 ('Student Innovation Showcase','Campus Events','2026-12-12','Open to all departments','Demo your class or side project at the student showcase.'),
 ('Winter Web Build Weekend','Hackathons','2026-12-05','Teams of 2–5 students','Build a useful campus web experience in a friendly weekend sprint.'),
 ('Community Climate Microgrant','Scholarships','2027-01-15','Student-led campus sustainability teams','Small project grants for measurable campus climate improvements.'),
 ('Research Poster Workshop','Workshops','2026-11-28','Undergraduate researchers','Practice turning a research question into a clear, readable poster.'),
 ('Campus Design Challenge','Competitions','2026-12-20','Open to all years','Pitch an inclusive improvement to a shared student space.'),
 ('Library Digital Archives Internship','Internships','2027-01-08','Computing, history or design students','Assist with metadata cleanup and an accessible digital exhibit.'),
 ('Peer Tutor Orientation','Seminars','2026-11-30','Students interested in peer teaching','Learn how to plan supportive, inclusive tutoring sessions.'),
 ('Student Startup Demo Night','Campus Events','2026-12-18','Open to all departments','Meet student founders and share an early idea or prototype.'),
 ('Open Data Visualization Sprint','Hackathons','2027-01-10','Teams welcome; beginner friendly','Create a clear visual story from a public civic dataset.'),
 ('Campus Wellbeing Ideas Fund','Other Opportunities','2027-01-22','Student clubs and project groups','Propose a small activity that helps students find community.'),
 ('Robotics Lab Open Evening','Workshops','2026-12-03','Beginners and experienced builders','Try sensors, simple controls and rapid prototyping with lab mentors.'),
 ('First-Year Peer Guide Applications','Internships','2027-01-12','Returning students','Apply to welcome new students and help them navigate campus resources.'),
]
ISSUES=[
 ('Demo: Study hall lights flicker','Electricity','North study hall, Room 204','Lights flicker near the back row during evening classes.','Normal','Under Review'),
 ('Demo: Water fountain not cooling','Water Supply','Library, ground floor','Fountain runs but the water is warm. Please check the cooling unit.','Low','Submitted'),
 ('Demo: Wi-Fi drops in seminar room','Internet / Wi-Fi','Science block, Seminar 3','Connection drops repeatedly during lectures.','High','Assigned'),
 ('Demo: Projector cable loose','Classroom Maintenance','Arts block, Room 18','Display cable disconnects if the desk is moved.','Normal','In Progress'),
 ('Demo: Lab sink drain is slow','Laboratory Issues','Chemistry lab, bench 6','Drain backs up during normal cleaning.','Normal','Submitted'),
 ('Demo: Broken path light','Electricity','West path near sports centre','One path light is out after sunset.','High','Under Review'),
 ('Demo: Refill station needs cleaning','Sanitation','Student centre, level 2','The refill station area needs a routine clean.','Low','Resolved'),
 ('Demo: Hostel laundry machine offline','Hostel Issues','West hostel, laundry room','Machine 4 shows an error and will not start.','Normal','Assigned'),
]
ITEMS=[
 ('Demo: Teal water bottle','Found','Bottle','Library second floor, study tables','2026-11-16','teal water bottle','bottle.svg','Open'),
 ('Demo: Wireless earbuds case','Lost','Electronics','Engineering atrium, near the stairs','2026-11-15','white case with two earbuds','earbuds.svg','Open'),
 ('Demo: Orange study notebook','Found','Books','North lecture hall, row C','2026-11-17','orange cover, graph paper inside','notebook.svg','Open'),
 ('Demo: Purple umbrella','Lost','Accessories','Student centre entrance','2026-11-14','purple canopy with curved wooden handle','umbrella.svg','Claim Pending'),
 ('Demo: Scientific calculator','Found','Electronics','Math building, Room 108','2026-11-13','grey calculator with green display','calculator.svg','Open'),
 ('Demo: Pink USB drive','Lost','Electronics','Computer lab, workstation 12','2026-11-17','pink flash drive with small key ring','flash-drive.svg','Open'),
 ('Demo: Teal bottle returned','Found','Bottle','Sports centre front desk','2026-11-10','teal insulated bottle with silver lid','bottle.svg','Returned'),
 ('Demo: Notebook found near cafe','Found','Books','Garden cafe, outdoor table','2026-11-12','small orange notebook, blank label inside','notebook.svg','Open'),
]

def main():
    with campus.app.app_context():
        c=campus.db(); ids={}
        for name,dept,year,skills,interests,availability,bio in PEOPLE:
            email='demo-'+name.split()[0].lower()+'@campusone.invalid'
            c.execute("INSERT OR IGNORE INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",('Demo · '+name,email,generate_password_hash(secrets.token_urlsafe(40)),'student',campus.now()))
            u=c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone(); uid=u['id']; ids[name]=uid
            c.execute('INSERT OR IGNORE INTO profiles(user_id,updated_at) VALUES(?,?)',(uid,campus.now()))
            c.execute('UPDATE profiles SET department=?,year=?,skills=?,interests=?,availability=?,bio=?,updated_at=? WHERE user_id=?',(dept,year,campus.json.dumps(skills),campus.json.dumps(interests),availability,bio,campus.now(),uid))
        admin_email='demo-office@campusone.invalid'; c.execute("INSERT OR IGNORE INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",('Demo · Campus Office',admin_email,generate_password_hash(secrets.token_urlsafe(40)),'admin',campus.now())); office=c.execute('SELECT id FROM users WHERE email=?',(admin_email,)).fetchone()['id']
        student_ids=list(ids.values())
        def add(module,owner,title,data,status='Open'):
            existing=c.execute('SELECT id FROM records WHERE module=? AND owner_id=? AND title=?',(module,owner,title)).fetchone()
            if existing:return existing['id']
            cur=c.execute('INSERT INTO records(module,kind,owner_id,title,data,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(module,campus.MODULES[module],owner,title,campus.json.dumps(data,ensure_ascii=False),status,campus.now(),campus.now())); rid=cur.lastrowid
            c.execute('INSERT INTO history(record_id,actor_id,status,note,created_at) VALUES(?,?,?,?,?)',(rid,owner,status,'Demo showcase entry',campus.now())); return rid
        project_ids=[]
        for i,(title,desc,skills,size,interest,availability) in enumerate(PROJECTS):
            project_ids.append(add('teams',student_ids[i],title,{'listing_type':'Create a team' if i<4 else 'Project seeking teammates','description':desc,'required_skills':skills,'team_size':size,'interests':[interest],'department':PEOPLE[i][1],'availability':availability,'experience':'Demo project · student-led'}))
        for team_idx,members in [(0,[1,3,6]),(1,[2,7,8]),(2,[4,5,9]),(3,[0,2,6])]:
            for member_idx in members:
                if member_idx==team_idx:continue
                team=project_ids[team_idx]; uid=student_ids[member_idx]
                c.execute("INSERT OR IGNORE INTO team_members(team_id,user_id,invited_by,role,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",(team,uid,student_ids[team_idx],PEOPLE[member_idx][2]+' contributor','Accepted',campus.now(),campus.now()))
        for i,(title,subject,topics,person) in enumerate(TUTORS):
            p=PEOPLE[next(k for k,x in enumerate(PEOPLE) if x[0]==person)]
            add('tutoring',ids[person],title,{'subject':subject,'topics':topics,'experience':p[6],'availability':p[5],'mode':'Either','department':p[1],'session_length':'60 minutes','group_size':'One to one'})
        for i,(title,dept,year,expertise,availability) in enumerate(MENTORS):
            p=PEOPLE[i]
            add('mentors',student_ids[i],title,{'department':dept,'year':year,'expertise':expertise,'interests':expertise,'experience':p[6],'availability':availability,'format':'Either','languages':'English · Demo profile'})
        for i,(title,category,deadline,eligibility,desc) in enumerate(OPPORTUNITIES):
            add('opportunities',office,title,{'category':category,'department':'All departments','deadline':deadline,'location':'Campus · Demo listing','registration_url':'','organizer':'Campus Office · Demo','eligibility':eligibility,'cost':'No fee listed','description':desc})
        for idx,(title,category,location,desc,urgency,status) in enumerate(ISSUES):
            add('issues',student_ids[idx%len(student_ids)],title,{'category':category,'location':location,'description':desc,'urgency':urgency,'when_observed':'Demo entry · November 2026','complaint_id':'DEMO-'+str(idx+1001)},status)
        for idx,(title,kind,category,location,date,detail,image,status) in enumerate(ITEMS):
            owner=student_ids[idx%len(student_ids)]
            add('lost-found',owner,title,{'type':kind,'category':category,'location':location,'date':date,'description':detail,'color_brand':detail,'photo_url':'/assets/lost-found/'+image,'contact_method':'CampusOne claim request · Demo listing'},status)
        c.commit()
        counts={m:c.execute('SELECT count(*) FROM records WHERE module=?',(m,)).fetchone()[0] for m in campus.MODULES}
        print('CampusOne showcase content is ready (demo data; fictional profiles/listings).')
        print(f"Demo member profiles: {len(PEOPLE)}")
        print('Module listing totals: '+', '.join(f'{m}={n}' for m,n in counts.items()))
        memberships=c.execute("SELECT count(*) FROM team_members WHERE status='Accepted'").fetchone()[0]
        print(f'Team memberships: {memberships}')

if __name__=='__main__': main()
