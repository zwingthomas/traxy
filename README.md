# Traxy — Activity & Habit Tracker

[![Live Demo](https://img.shields.io/badge/demo-traxy.app-blue)](https://www.traxy.app)

Traxy is a lightweight, **social** habit-tracking app built with Python (Flask/FastAPI), Tailwind CSS, and vanilla JavaScript. Record daily activities on a calendar grid, share selected trackers with friends, and manage real-time friend requests—all without page reloads.

---

## 🚀 Live Demo

Browse the public profile of **zwingthomas** at  
🔗 https://www.traxy.app/u/zwingthomas

---

## 🔑 Key Features (future looking)

### Trackers Calendar  
- **Boolean**, **Counter**, or **Numeric-Input** trackers  
- Date-range views: This Week / This Month / Last 365 Days  
- Heatmap-style coloring proportional to your goal  
- Click / long-press (desktop & mobile) to toggle or reset daily entries  

### Privacy & Sharing  
- **Private**, **Friends-only**, or **Public** visibility per tracker  
- Public profile pages with **dynamic friend-count badge**  
- “Add Friend” badge when viewing someone you’re not yet connected with  

### Real-Time Friends & Notifications  
- **Friend requests** flow: send, accept, dismiss  
- **“Inbox” overlay** on your Dashboard—new requests push in without refresh  
- **Drag-and-drop** to remove friends: toggle delete-mode, drag avatar into trash icon  

### User Account Management  
- Sign up / Log in with session-based auth  
- Change or reset password (email token flow): coming soon 
- Profile fields: First Name / Last Name / Email / Phone: coming soon
- Profile pictures (avatar upload & resize): coming soon
- Timezone sync (auto-detect and store on login)

---

## 🏗️ Architecture

1. **Backend**  
   - Python 3.9+ with **Flask** (front-end proxy) and **FastAPI** (core API)  
   - SQLAlchemy ORM → PostgreSQL / Cloud SQL  
   - Notifications & friend-requests stored in a `notifications` table  
   - Google Pub/Sub + Server-Sent Events for real-time inbox updates  

2. **Frontend**  
   - **Tailwind CSS** for utility-first styling  
   - Vanilla JS + **SortableJS** for drag-and-drop UI  
   - Calendar rendering in `/static/js/calendar.js`  
   - Friend-overlay & delete-mode in `/static/js/friends.js`  

3. **Deployment**  
   - Containerized via Docker → Cloud Run (or VM + systemd)  
   - HTTPS everywhere (Let’s Encrypt)  
   - CI/CD pipelines for migrations & tests  

---

# 🛠️ Roadmap

###
## MUST HAVES
###


June 14

**6 - 12 hours** - Database migration to VM

**6 - 10 hours** - Make adding friends, friend requests. Have another icon similar to friend badge next to it with friend requests


June 21

**2 hours** - See your profile as you view it, publicly, and as friends will see it

**2 hours** - Have First Name / Last Name / Email / Phone

**2 hours** - Make dashboard endpoint be /u/active-user-username instead of /dashboard

**12 hours** - Allow people to change their password / forget their password

**4 hours** - Show error dynamically if username is already taken when signing up


June 28

**1 hour** - Fix tracker's overlap on smaller screens

**2 - 3 hours** - Fix weekly, monthly, etc coloring for trackers

**2 hours** - Check on security (there may be a massive spike here)

**6 hours** - Timezones

**3 hours** - Fix bug: On mobile it is too easy to move around trackers


July 5

**6 - 10 hours** - Profile pictures

**10 hours** - Implement testing frameworks


July 12

**20 hours** - Implement testing frameworks





###
## NICE TO HAVE
###


July 19

**8 hours** - Make username changable along with user's URL endpoint

**12 hours** - Be able to group trackers and have a overview as well


July 26

**15 - 25 hours** - Shared trackers


August 2

**20 - 30 hours** - Be able to make groups of friends and set challenges


August 9

**4 - 6 hours** - Sharing specific trackers

**4 - 6 hours** - Streaks


August 16

**8 hours** - Debt/Overages around trackers

**4 hours** - Moods

**12 hours** - Journal for each tracker 


August 23

**3 hours** - Return and rerender only the tracker updated when updating a tracker

**8 - 16 hours** - Visual rewards for goal accomplishment


August 30, September 6, September 13

**60 hours** - ChatGPT integration


September 20, 27

**20 hours** - Write tests




###
## LAST STEPS
###


Oct, Nov, Dec

**60 - 80 hours** hours - Journalling/blog epic


2026

**200 hours** - Write frontend for iOS and Android