CREATE OR REPLACE PROCEDURE GMAIL_ANALYTICS.CORE.GENERATE_SYNTHETIC_GMAIL_DATA()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python','pandas')
HANDLER = 'main'
EXECUTE AS CALLER
AS '
import pandas as pd
import random
import datetime
import json

def main(session):
    random.seed(42)

    NUM_CONTACTS = 320
    NUM_THREADS = 230
    TARGET_MESSAGES = 1100
    START_DATE = datetime.datetime(2025, 3, 22)
    END_DATE = datetime.datetime(2026, 3, 21)
    TOTAL_SECONDS = int((END_DATE - START_DATE).total_seconds())

    first_names = [
        "James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
        "David","Elizabeth","William","Barbara","Richard","Susan","Joseph","Jessica",
        "Thomas","Sarah","Christopher","Karen","Charles","Lisa","Daniel","Nancy",
        "Matthew","Betty","Anthony","Margaret","Mark","Sandra","Donald","Ashley",
        "Steven","Dorothy","Andrew","Kimberly","Paul","Emily","Joshua","Donna",
        "Kenneth","Michelle","Kevin","Carol","Brian","Amanda","George","Melissa",
        "Timothy","Deborah","Edward","Stephanie","Ronald","Rebecca","Jason","Sharon"
    ]
    last_names = [
        "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
        "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
        "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
        "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker",
        "Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill",
        "Flores","Green","Adams","Nelson","Baker","Hall","Rivera","Campbell",
        "Mitchell","Carter","Roberts","Gomez","Phillips","Evans","Turner","Diaz"
    ]
    personal_domains = ["gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com","protonmail.com","aol.com","mail.com"]
    business_domains = [
        "acme-corp.com","techsolutions.io","globalfinance.com","innovatetech.co",
        "nexusgroup.com","pinnaclesystems.com","vanguardtech.com","horizonlabs.com",
        "atlasdata.com","quantumworks.io","stratosphereai.com","datapulse.com",
        "cloudnexus.com","corestack.io","blueshift.tech","ironbridge.com",
        "apexdigital.com","fusionanalytics.com","northstardata.com","redwoodtech.com"
    ]
    alert_senders = [
        ("Snowflake Alerts","alerts@snowflakecomputing.com"),
        ("Snowflake Monitoring","monitoring@snowflakecomputing.com"),
        ("AWS Notifications","no-reply@sns.amazonaws.com"),
        ("Google Cloud","noreply@google.com"),
        ("GitHub","noreply@github.com"),
        ("Datadog Alerts","alert@dtdg.co"),
        ("PagerDuty","no-reply@pagerduty.com"),
        ("Jira","jira@atlassian.com"),
        ("Slack","notification@slack.com"),
        ("Grafana Alerts","alerts@grafana.net")
    ]
    promo_senders = [
        ("LinkedIn","messages-noreply@linkedin.com"),
        ("Medium Daily Digest","noreply@medium.com"),
        ("Udemy","no-reply@e.udemymail.com"),
        ("AWS Events","no-reply@awscloud.com"),
        ("Snowflake Summit","events@snowflake.com"),
        ("OReilly Media","mailer@oreilly.com"),
        ("TechCrunch","newsletter@techcrunch.com"),
        ("Coursera","no-reply@coursera.org"),
        ("Stack Overflow","do-not-reply@stackoverflow.email"),
        ("DataCamp","hello@datacamp.com")
    ]
    support_senders = [
        ("Snowflake Support","support@snowflake.com"),
        ("AWS Support","no-reply@support.aws.amazon.com"),
        ("Zendesk","support@zendesk.com"),
        ("Salesforce Support","support@salesforce.com"),
        ("Microsoft Support","msa@communication.microsoft.com")
    ]
    finance_senders = [
        ("Expensify","concierge@expensify.com"),
        ("QuickBooks","intuit@notification.intuit.com"),
        ("Stripe","receipts@stripe.com"),
        ("PayPal","service@paypal.com"),
        ("Chase Bank","no-reply@alertsp.chase.com")
    ]
    suspicious_domains = [
        "secure-bankofamerica.xyz","apple-id-verify.net","paypa1-secure.com",
        "amaz0n-security.com","g00gle-account.com","micros0ft-verify.com",
        "snowf1ake-alert.com","urgent-action-required.com","account-verify-now.com",
        "free-prize-winner.com"
    ]

    contacts = []
    cid = 1
    used_emails = set()

    def make_email(fn, ln, domain, suffix=""):
        return f"{fn.lower()}.{ln.lower()}{suffix}@{domain}"

    def add_contact(email, name, domain, ctype, internal=False):
        nonlocal cid
        if email in used_emails:
            return
        used_emails.add(email)
        ts = START_DATE + datetime.timedelta(seconds=random.randint(0, TOTAL_SECONDS))
        contacts.append({"CONTACT_ID": cid, "EMAIL": email, "DISPLAY_NAME": name,
            "DOMAIN": domain, "CONTACT_TYPE": ctype, "IS_INTERNAL": internal,
            "CREATED_AT": ts.isoformat(), "UPDATED_AT": ts.isoformat()})
        cid += 1

    for _ in range(130):
        fn, ln = random.choice(first_names), random.choice(last_names)
        dom = random.choice(business_domains)
        add_contact(make_email(fn, ln, dom, str(random.randint(1,99)) if random.random()<0.3 else ""),
            f"{fn} {ln}", dom, "business", random.random() < 0.3)

    for _ in range(90):
        fn, ln = random.choice(first_names), random.choice(last_names)
        dom = random.choice(personal_domains)
        add_contact(make_email(fn, ln, dom, str(random.randint(1,99)) if random.random()<0.3 else ""),
            f"{fn} {ln}", dom, "personal", False)

    for name, email in alert_senders:
        add_contact(email, name, email.split("@")[1], "alert", False)
    for name, email in promo_senders:
        add_contact(email, name, email.split("@")[1], "promotion", False)
    for name, email in support_senders:
        add_contact(email, name, email.split("@")[1], "support", False)
    for name, email in finance_senders:
        add_contact(email, name, email.split("@")[1], "finance", False)

    suspicious_names = ["Security Team","Account Verification","Prize Department",
        "IT Department","Bank Security","Apple Support","Urgent Notice",
        "Admin Office","Helpdesk","Lottery Winners"]
    for i in range(35):
        sn = suspicious_names[i % len(suspicious_names)]
        sd = suspicious_domains[i % len(suspicious_domains)]
        add_contact(f"{sn.lower().replace('' '',''.'')}{i}@{sd}", sn, sd, "suspicious", False)

    while len(contacts) < NUM_CONTACTS:
        fn, ln = random.choice(first_names), random.choice(last_names)
        dom = random.choice(personal_domains + business_domains)
        ct = "personal" if dom in personal_domains else "business"
        add_contact(make_email(fn, ln, dom, str(random.randint(100,999))),
            f"{fn} {ln}", dom, ct, False)

    system_labels = [
        ("INBOX","system",None,"labelShow","INBOX"),
        ("SENT","system",None,"labelShow","SENT"),
        ("DRAFTS","system",None,"labelShow","DRAFT"),
        ("SPAM","system",None,"labelHide","SPAM"),
        ("TRASH","system",None,"labelHide","TRASH"),
        ("STARRED","system",None,"labelShow","STARRED"),
        ("IMPORTANT","system",None,"labelShow","IMPORTANT"),
        ("UNREAD","system",None,"labelShow","UNREAD"),
        ("CATEGORY_PRIMARY","system",None,"labelHide","CATEGORY_PERSONAL"),
        ("CATEGORY_SOCIAL","system",None,"labelHide","CATEGORY_SOCIAL"),
        ("CATEGORY_PROMOTIONS","system",None,"labelHide","CATEGORY_PROMOTIONS"),
        ("CATEGORY_UPDATES","system",None,"labelHide","CATEGORY_UPDATES"),
        ("CATEGORY_FORUMS","system",None,"labelHide","CATEGORY_FORUMS"),
    ]
    user_labels = [
        ("Work","user","#4285f4","show"),
        ("Personal","user","#34a853","show"),
        ("Finance","user","#fbbc05","show"),
        ("Travel","user","#ea4335","show"),
        ("Projects","user","#673ab7","show"),
        ("Receipts","user","#ff6d00","show"),
        ("To Follow Up","user","#e91e63","show"),
        ("Waiting On","user","#00bcd4","show"),
        ("Newsletters","user","#795548","show"),
        ("Snowflake","user","#29b5e8","show"),
        ("Data Engineering","user","#9c27b0","show"),
        ("Meetings","user","#3f51b5","show"),
        ("Urgent","user","#f44336","show"),
        ("Archive","user","#607d8b","show"),
        ("Clients","user","#009688","show"),
    ]

    labels = []
    lid = 1
    for name, lt, color, vis, gid in system_labels:
        labels.append({"LABEL_ID": lid, "LABEL_NAME": name, "LABEL_TYPE": lt,
            "COLOR": color, "VISIBILITY": vis, "GMAIL_LABEL_ID": gid,
            "CREATED_AT": START_DATE.isoformat()})
        lid += 1
    for name, lt, color, vis in user_labels:
        labels.append({"LABEL_ID": lid, "LABEL_NAME": name, "LABEL_TYPE": lt,
            "COLOR": color, "VISIBILITY": vis, "GMAIL_LABEL_ID": f"Label_{lid}",
            "CREATED_AT": START_DATE.isoformat()})
        lid += 1

    label_name_to_id = {l["LABEL_NAME"]: l["LABEL_ID"] for l in labels}

    topics = [
        "Data Pipeline Optimization","ML Model Deployment","Snowpark Migration",
        "Data Warehouse Modernization","Real-time Analytics Dashboard",
        "ETL Pipeline Refactoring","Cloud Cost Optimization","Security Audit",
        "API Integration","Microservices Architecture","Database Performance Tuning",
        "CI/CD Pipeline","Data Governance Framework","Customer Segmentation",
        "Anomaly Detection System","Data Lake Architecture","Stream Processing",
        "A/B Testing Framework","Data Quality Monitoring","Infrastructure as Code",
        "Kubernetes Cluster Setup","Feature Store Implementation","dbt Transformation Layer",
        "Iceberg Table Migration","Dynamic Tables Rollout"
    ]
    companies = [
        "Acme Corp","TechSolutions","GlobalFinance","InnovateTech",
        "NexusGroup","PinnacleSystems","VanguardTech","HorizonLabs",
        "AtlasData","QuantumWorks","StratosphereAI","DataPulse",
        "CloudNexus","CoreStack","BlueShift","IronBridge"
    ]
    warehouses = ["ANALYTICS_WH","ETL_WH","LOADING_WH","TRANSFORM_WH","DEV_WH","REPORTING_WH"]
    sf_tasks = ["DAILY_ETL","HOURLY_SYNC","DATA_QUALITY_CHECK","MODEL_REFRESH","REPORT_GEN","SNOWPIPE_LOAD"]
    months_list = ["January","February","March","April","May","June","July","August","September","October","November","December"]

    def fill_tmpl(t):
        r = t
        r = r.replace("{q}", str(random.randint(1,4)))
        r = r.replace("{n}", str(random.randint(100,9999)))
        r = r.replace("{pct}", str(random.choice([10,15,20,25,30,40,50])))
        r = r.replace("{amount}", f"{random.uniform(50,5000):.2f}")
        r = r.replace("{year}", str(random.choice([2025,2026])))
        r = r.replace("{company}", random.choice(companies))
        r = r.replace("{company2}", random.choice(companies))
        r = r.replace("{topic}", random.choice(topics))
        r = r.replace("{wh}", random.choice(warehouses))
        r = r.replace("{task}", random.choice(sf_tasks))
        r = r.replace("{month}", random.choice(months_list))
        r = r.replace("{date}", (START_DATE + datetime.timedelta(days=random.randint(0,365))).strftime("%Y-%m-%d"))
        r = r.replace("{n2}", str(random.randint(1,255)))
        r = r.replace("{name}", random.choice(first_names))
        return r

    subject_templates = {
        "business": [
            "Q{q} Revenue Report - {company}","Partnership Proposal: {company} x {company2}",
            "Meeting Notes - {topic}","Contract Review: {company} Agreement",
            "Budget Approval Request - {topic}","RFP Response: {topic}",
            "Client Onboarding: {company}","Strategic Planning Session - Q{q}",
            "Board Meeting Agenda - {month}","Vendor Evaluation: {company}",
            "Market Analysis: {topic}","Due Diligence Report: {company}",
        ],
        "work": [
            "Sprint {n} Planning","Code Review: {topic}",
            "Deploy to Production: {topic}","Bug Report: {topic}",
            "Feature Request: {topic}","1:1 Meeting Agenda",
            "Team Retrospective - Sprint {n}","Pull Request: {topic}",
            "Architecture Decision: {topic}","On-call Rotation - {month}",
            "Incident Postmortem: {topic}","Release Notes v{n}",
        ],
        "personal": [
            "Weekend Plans?","Happy Birthday!","Dinner Reservation Confirmation",
            "Re: Vacation Photos","Book Recommendation: {topic}","Catch up soon?",
            "Moving Announcement","Holiday Party RSVP","Game Night This Friday?",
            "Concert Tickets Available","Gym Membership Renewal","Family Reunion Planning",
        ],
        "alerts": [
            "[Snowflake] Warehouse {wh} credit usage exceeded threshold",
            "[Snowflake] Task {task} failed - {topic}",
            "[Snowflake] Storage usage alert - {n}TB consumed",
            "[Snowflake] Query performance degradation detected",
            "[Snowflake] New login from unrecognized device",
            "[Snowflake] Credit quota 80% consumed",
            "[Snowflake] Pipe SNOWPIPE_LOAD error: {topic}",
            "[Snowflake] Resource monitor DAILY_LIMIT triggered",
            "[AWS] EC2 Instance Alert: {topic}",
            "[GitHub] Security vulnerability in {topic}",
            "[Datadog] Alert: {topic} - Critical",
            "[PagerDuty] Incident #{n}: {topic}",
        ],
        "promotions": [
            "{pct}% off - Limited Time Offer","New Course: {topic}",
            "Your Weekly Digest","Invitation: {topic} Conference 2026",
            "Free Trial: {topic}","Webinar: {topic} Best Practices",
            "Early Bird: Snowflake Summit 2026","Special Offer for Data Professionals",
            "Learn {topic} in 30 Days","Top Stories This Week",
        ],
        "support": [
            "Case #{n}: {topic} - Update","Your ticket has been resolved",
            "Re: Issue with {topic}","Scheduled Maintenance Notice - {date}",
            "How was your support experience?","Support Case Escalation: {topic}",
            "System Status Update: {topic}","Knowledge Base Update: {topic}",
        ],
        "finance": [
            "Invoice #{n} from {company}","Payment Confirmation - ${amount}",
            "Expense Report: {month} {year}","Budget Update - Q{q} {year}",
            "Your {month} Statement is Ready","Subscription Renewal: {company}",
            "Tax Document Available - {year}","Purchase Order #{n} Approved",
        ],
    }

    body_templates = {
        "business": [
            "Hi team,\\n\\nPlease find attached the {topic} report for your review. Key highlights:\\n\\n- Revenue increased by {pct}% compared to last quarter\\n- Customer acquisition cost decreased\\n- Market share grew in key segments\\n\\nBest regards,\\n{name}",
            "Dear {name},\\n\\nFollowing up on our discussion regarding {topic}. I have prepared the initial analysis and would like to schedule a call.\\n\\nPlease let me know your availability.\\n\\nThanks,\\n{name}",
            "Team,\\n\\nQuick update on {topic}:\\n\\n1. Phase 1 complete\\n2. Phase 2 kickoff next Monday\\n3. Budget tracking within 5%\\n\\nRegards,\\n{name}",
        ],
        "work": [
            "Hey team,\\n\\nPushed changes for {topic} to feature branch:\\n\\n- Refactored data processing pipeline\\n- Added unit tests (coverage 87%)\\n- Updated docs\\n\\nPlease review.\\n\\n{name}",
            "Deploy for {topic} scheduled tonight 11 PM EST:\\n\\n- Performance improvements (30% faster)\\n- Bug fix for null handling\\n- Updated connector version\\n\\nOn-call notified.\\n\\n{name}",
            "Found a bug in {topic}. Incorrect aggregation with NULL filters.\\n\\nHotfix PR created. Can someone review urgently?\\n\\n{name}",
        ],
        "personal": [
            "Hey! Free this weekend? Coffee and catch up?\\n\\n{name}",
            "Thanks for the recommendation! Great read so far.\\n\\nDid you see the news about {topic}?\\n\\n{name}",
            "Sharing photos from the trip. Amazing time!\\n\\nHope you are doing well.\\n\\n{name}",
        ],
        "alerts": [
            "ALERT: Warehouse {wh} consumed {pct}% of credits.\\n\\nUsage: {n} credits\\nBudget: 10000\\nProjected: 12500\\n\\nReview long-running queries.\\n\\n-- Snowflake Monitoring",
            "TASK FAILURE\\n\\nTask: {task}\\nDB: PRODUCTION.ETL\\nError: Timeout 3600s\\nTime: {date} 03:45 UTC\\n\\nInvestigate and retry.\\n\\n-- Snowflake Scheduler",
            "SECURITY ALERT\\n\\nNew login:\\nIP: 192.168.{n2}.{n2}\\nLocation: San Francisco\\nTime: {date} 14:22 UTC\\n\\nChange password if not you.\\n\\n-- Snowflake Security",
            "RESOURCE MONITOR\\n\\nMonitor: DAILY_LIMIT\\nWarehouse: {wh}\\nAction: Suspend\\nCredits: {n}\\n\\n-- Snowflake Monitor",
        ],
        "promotions": [
            "Get {pct}% off all courses!\\n\\nFeatured:\\n- Advanced {topic}\\n- {topic} Masterclass\\n\\nCode: SAVE{pct}\\n\\nHappy learning!",
            "{topic} Conference 2026\\nJune 15-17, San Francisco\\n\\nEarly bird open. Save $200 before April 30.",
        ],
        "support": [
            "Case #{n} for {topic} assigned.\\n\\nStatus: In Progress\\nPriority: High\\nETA: 24-48 hours\\n\\n-- Support Team",
            "Ticket #{n} resolved.\\n\\nSolution: {topic} config updated.\\n\\nReply to reopen if needed.",
        ],
        "finance": [
            "Invoice #{n}\\n\\nTo: {company}\\nDate: {date}\\nDue: Net 30\\n\\n- {topic}: ${amount}\\n- Platform Fee: $99\\n\\nThank you.",
            "Statement for {month} ready.\\n\\nCharges: ${amount}\\nDue: {date}\\nStatus: Current",
        ],
    }

    suspicious_bodies = [
        "URGENT: Account compromised. Verify identity immediately or face permanent suspension.\\n\\nVerify: http://secure-verify-account.com/login\\n\\nSecurity Team",
        "Congratulations! You won $50000 in our sweepstakes!\\n\\nProvide: full name, bank account, SSN.\\n\\nReply in 48 hours.",
        "Unusual activity on your Snowflake account. Password expires in 2 hours.\\n\\nReset: http://snowf1ake-security.com/reset\\n\\nSnowflake Security",
        "Payment method declined. Update billing now.\\n\\nUpdate: http://bill1ng-update.com/payment",
        "CEO here. Process wire transfer $15000 urgently. Confidential.\\n\\nBank: International Trust\\nAccount: 8847291033\\n\\nConfirm.",
    ]

    categories = ["business","work","personal","alerts","promotions","support","finance"]
    cat_weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.08, 0.07]

    threads = []
    thread_cats = random.choices(categories, weights=cat_weights, k=NUM_THREADS)
    for i, cat in enumerate(thread_cats):
        subj = fill_tmpl(random.choice(subject_templates[cat]))
        t_start = START_DATE + datetime.timedelta(seconds=random.randint(0, TOTAL_SECONDS))
        threads.append({"THREAD_ID": i+1, "SUBJECT": subj, "CATEGORY": cat,
            "STARTED_AT": t_start.isoformat(), "LAST_MESSAGE_AT": t_start.isoformat(),
            "MESSAGE_COUNT": 0, "IS_MUTED": random.random() < 0.05,
            "CREATED_AT": t_start.isoformat()})

    msg_per_thread = []
    for i in range(NUM_THREADS):
        if threads[i]["CATEGORY"] in ("alerts","promotions","finance"):
            c = random.randint(1, 3)
        elif threads[i]["CATEGORY"] == "support":
            c = random.randint(2, 8)
        else:
            c = random.randint(1, 12)
        msg_per_thread.append(c)
    total_assigned = sum(msg_per_thread)
    diff = TARGET_MESSAGES - total_assigned
    while diff > 0:
        idx = random.randint(0, NUM_THREADS - 1)
        msg_per_thread[idx] += 1
        diff -= 1
    while diff < 0:
        candidates = [i for i in range(NUM_THREADS) if msg_per_thread[i] > 1]
        if not candidates:
            break
        idx = random.choice(candidates)
        msg_per_thread[idx] -= 1
        diff += 1

    cat_to_contacts = {
        "business": [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "business"],
        "work": [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "business"],
        "personal": [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "personal"],
        "alerts": [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "alert"],
        "promotions": [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "promotion"],
        "support": [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "support"],
        "finance": [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "finance"],
    }
    suspicious_ids = [c["CONTACT_ID"] for c in contacts if c["CONTACT_TYPE"] == "suspicious"]
    all_cids = [c["CONTACT_ID"] for c in contacts]
    me_id = 1

    cat_to_labels = {
        "business": ["INBOX","IMPORTANT","Work","CATEGORY_PRIMARY"],
        "work": ["INBOX","Work","Data Engineering","CATEGORY_PRIMARY"],
        "personal": ["INBOX","Personal","CATEGORY_PRIMARY"],
        "alerts": ["INBOX","IMPORTANT","Snowflake","CATEGORY_UPDATES"],
        "promotions": ["CATEGORY_PROMOTIONS","Newsletters"],
        "support": ["INBOX","CATEGORY_UPDATES"],
        "finance": ["INBOX","Finance","Receipts","CATEGORY_UPDATES"],
    }

    attach_patterns = {
        "business": [
            ("Quarterly_Report_Q{q}.pdf","application/pdf",100000,5000000),
            ("Presentation.pptx","application/vnd.ms-powerpoint",500000,15000000),
            ("Budget_{year}.xlsx","application/vnd.ms-excel",50000,2000000),
            ("Contract.pdf","application/pdf",200000,8000000),
            ("Meeting_Notes.docx","application/vnd.ms-word",30000,500000),
        ],
        "work": [
            ("architecture_diagram.png","image/png",100000,3000000),
            ("error_log.txt","text/plain",5000,500000),
            ("test_results.csv","text/csv",10000,1000000),
            ("deploy_config.yaml","application/x-yaml",1000,50000),
            ("screenshot.png","image/png",50000,2000000),
        ],
        "personal": [
            ("photo.jpg","image/jpeg",500000,8000000),
            ("recipe.pdf","application/pdf",50000,500000),
        ],
        "alerts": [],
        "promotions": [
            ("event_brochure.pdf","application/pdf",500000,5000000),
        ],
        "support": [
            ("diagnostic_report.zip","application/zip",1000000,20000000),
            ("system_logs.txt","text/plain",50000,5000000),
        ],
        "finance": [
            ("invoice.pdf","application/pdf",50000,500000),
            ("receipt.pdf","application/pdf",30000,200000),
            ("statement.pdf","application/pdf",100000,2000000),
            ("expense_report.xlsx","application/vnd.ms-excel",50000,1000000),
        ],
    }

    messages = []
    attachments = []
    label_maps = []
    mid = 1
    aid = 1

    for t_idx in range(NUM_THREADS):
        thread = threads[t_idx]
        cat = thread["CATEGORY"]
        mc = msg_per_thread[t_idx]
        t_start = datetime.datetime.fromisoformat(thread["STARTED_AT"])
        sender_pool = cat_to_contacts.get(cat, cat_to_contacts["business"])
        if not sender_pool:
            sender_pool = all_cids[:10]
        thread_sender = random.choice(sender_pool)

        for m_idx in range(mc):
            sender = me_id if (mc > 1 and m_idx % 2 == 1) else thread_sender
            msg_time = t_start + datetime.timedelta(minutes=m_idx * random.randint(5, 180), seconds=random.randint(0, 59))
            if msg_time > END_DATE:
                msg_time = END_DATE - datetime.timedelta(minutes=random.randint(1, 60))

            is_suspicious = False
            spam_score = round(random.uniform(0, 0.15), 4)
            phishing_ind = None

            if random.random() < 0.04 and cat in ("promotions","business","personal"):
                is_suspicious = True
                spam_score = round(random.uniform(0.6, 0.99), 4)
                phishing_ind = json.dumps({"urgency": random.random() < 0.8,
                    "suspicious_links": random.random() < 0.7,
                    "impersonation": random.random() < 0.5,
                    "request_credentials": random.random() < 0.6,
                    "mismatched_domain": True})
                sender = random.choice(suspicious_ids)
                body = fill_tmpl(random.choice(suspicious_bodies))
            else:
                bt = body_templates.get(cat, body_templates["business"])
                body = fill_tmpl(random.choice(bt))

            num_recip = 1 if cat in ("alerts","promotions","finance") else random.randint(1, 4)
            pool = [c for c in all_cids if c != sender]
            recips = random.sample(pool, min(num_recip, len(pool)))
            to_ids = recips[:1]
            cc_ids = recips[1:] if len(recips) > 1 else []

            has_att = False
            if attach_patterns.get(cat) and random.random() < 0.25:
                has_att = True
                for _ in range(random.randint(1, 2)):
                    pat = random.choice(attach_patterns[cat])
                    fn = fill_tmpl(pat[0]).replace(" ", "_")
                    attachments.append({"ATTACHMENT_ID": aid, "MESSAGE_ID": mid,
                        "FILENAME": fn, "CONTENT_TYPE": pat[1],
                        "SIZE_BYTES": random.randint(pat[2], pat[3]),
                        "IS_INLINE": random.random() < 0.1,
                        "GMAIL_ATTACHMENT_ID": f"ANGjdJ{random.randint(100000,999999)}",
                        "CREATED_AT": msg_time.isoformat()})
                    aid += 1

            snippet = body[:150].replace("\\n", " ").strip()
            is_read = random.random() < 0.75
            is_starred = random.random() < 0.1
            is_sent = sender == me_id

            messages.append({
                "MESSAGE_ID": mid,
                "THREAD_ID": thread["THREAD_ID"],
                "GMAIL_MESSAGE_ID": f"msg-{mid:06d}-{''''.join(random.choices(''abcdef0123456789'', k=8))}",
                "SENDER_CONTACT_ID": sender,
                "TO_CONTACT_IDS": json.dumps(to_ids),
                "CC_CONTACT_IDS": json.dumps(cc_ids),
                "BCC_CONTACT_IDS": json.dumps([]),
                "SUBJECT": thread["SUBJECT"] if m_idx == 0 else f"Re: {thread[''SUBJECT'']}",
                "SNIPPET": snippet,
                "BODY_TEXT": body,
                "BODY_HTML": f"<div>{body}</div>",
                "SENT_AT": msg_time.isoformat(),
                "RECEIVED_AT": (msg_time + datetime.timedelta(seconds=random.randint(1, 30))).isoformat(),
                "IS_READ": is_read,
                "IS_STARRED": is_starred,
                "IS_DRAFT": False,
                "IS_SENT": is_sent,
                "IS_TRASH": random.random() < 0.02,
                "IS_SPAM": is_suspicious and random.random() < 0.5,
                "HAS_ATTACHMENTS": has_att,
                "CATEGORY": cat,
                "IMPORTANCE": "high" if cat in ("alerts","finance") or is_starred else ("low" if cat == "promotions" else "normal"),
                "SPAM_SCORE": spam_score,
                "IS_SUSPICIOUS": is_suspicious,
                "PHISHING_INDICATORS": phishing_ind,
                "HEADERS": json.dumps({"Message-ID": f"<msg-{mid}@mail.gmail.com>", "X-Mailer": "Gmail API"}),
                "RAW_SIZE_BYTES": len(body.encode()) + random.randint(500, 2000),
                "GMAIL_HISTORY_ID": str(random.randint(100000, 999999)),
                "CREATED_AT": msg_time.isoformat(),
                "UPDATED_AT": msg_time.isoformat(),
            })

            base_labels = cat_to_labels.get(cat, ["INBOX"])
            msg_lbls = list(base_labels)
            if not is_read:
                msg_lbls.append("UNREAD")
            if is_starred:
                msg_lbls.append("STARRED")
            if is_sent:
                msg_lbls.append("SENT")
            if is_suspicious:
                msg_lbls.append("SPAM")
            if random.random() < 0.08:
                msg_lbls.append("To Follow Up")
            if random.random() < 0.05:
                msg_lbls.append("Meetings")

            seen_lbl = set()
            for lname in msg_lbls:
                if lname in label_name_to_id and lname not in seen_lbl:
                    seen_lbl.add(lname)
                    label_maps.append({"MESSAGE_ID": mid, "LABEL_ID": label_name_to_id[lname],
                        "APPLIED_AT": msg_time.isoformat()})
            mid += 1

        threads[t_idx]["LAST_MESSAGE_AT"] = messages[-1]["SENT_AT"]
        threads[t_idx]["MESSAGE_COUNT"] = mc

    contacts_df = pd.DataFrame(contacts)
    session.write_pandas(contacts_df, "EMAIL_CONTACTS", database="GMAIL_ANALYTICS", schema="CORE",
        auto_create_table=False, overwrite=True, quote_identifiers=False)

    labels_df = pd.DataFrame(labels)
    session.write_pandas(labels_df, "EMAIL_LABELS", database="GMAIL_ANALYTICS", schema="CORE",
        auto_create_table=False, overwrite=True, quote_identifiers=False)

    threads_df = pd.DataFrame(threads)
    session.write_pandas(threads_df, "EMAIL_THREADS", database="GMAIL_ANALYTICS", schema="CORE",
        auto_create_table=False, overwrite=True, quote_identifiers=False)

    messages_df = pd.DataFrame(messages)
    session.write_pandas(messages_df, "EMAIL_MESSAGES", database="GMAIL_ANALYTICS", schema="CORE",
        auto_create_table=False, overwrite=True, quote_identifiers=False)

    if attachments:
        attachments_df = pd.DataFrame(attachments)
        session.write_pandas(attachments_df, "EMAIL_ATTACHMENTS", database="GMAIL_ANALYTICS", schema="CORE",
            auto_create_table=False, overwrite=True, quote_identifiers=False)

    label_maps_df = pd.DataFrame(label_maps)
    session.write_pandas(label_maps_df, "EMAIL_MESSAGE_LABEL_MAP", database="GMAIL_ANALYTICS", schema="CORE",
        auto_create_table=False, overwrite=True, quote_identifiers=False)

    return f"Generated: {len(contacts)} contacts, {len(threads)} threads, {len(messages)} messages, {len(attachments)} attachments, {len(labels)} labels, {len(label_maps)} label mappings"
';