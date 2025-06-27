# 📁 static/ — Frontend Styling, Assets & Client-Side Logic

The static/ folder provides all **client-facing visual and behavioral elements** of the di6tpp web application. 
It includes:

    Images (e.g, logo)

    JavaScript to connect frontend interactions with backend API routes

    All files in this folder are linked via HTML templates in the templates/ directory.

    CSS — Styling & Layouts

All files in this folder are linked through Jinja2 templates in the templates/ directory.

## File Summary

Static File  Referenced In   Purpose

admin_style.css     layoutAdminPage.html    Styles the admin dashboard (sidebar, cards, forms)

adminscript.js      Admin templates  Allows admins to view and change private data

login_style.css     login.html      Visual styling for login screen
                    
loginscript.js  login.html  Form logic and login authentication 

style.css   layout_homepage.html    Shared layout for main user pages
                    
scripts.js  User templates VM creation logic and dynamic form submission

logo.png  Navbar (in all logged in user templates) logo of the project to style navbar


## css/ CSS files are organized by layout or purpose:

### css/admin_style.css

Applied via layoutAdminPage.html

Styles the admin sidebar, form cards, user/credential lists

Responsive design with hover states and button interactions

---

### css/login_style.css

Used only in login.html

Features a cyberpunk visual style (green-on-black)

Contains flicker animation via @keyframes

Enhances visual distinction of the login experience

---

### css/style.css

Used across general user pages (via layout_homepage.html)

Styles the homepage, VM listings, form containers, header/navbar, and buttons

Includes:

.VM-card for listing created VMs with action buttons

.error-box to warning user for wrong format input fields 

form enhancements for layout and readability

logo.png- Appears in the top-left corner on the navbar of all pages using layout_homepage.html

Helps brand the di6tpp interface visually

### images/

logo.png

Displayed on the top-left of the navbar in all user pages

Injected via:

<img src="/static/images/logo.png" alt="Logo">

Reinforces the name of the project

---

## js/ JavaScript does the API Integration & Frontend Logic

This folder includes all JS files that bridge the frontend templates with backend FastAPI endpoints, supporting async logic via fetch().

### js/adminscript.js

Used by admin-related pages (createUser.html, token_keys.html) and included via layoutAdminPage.html.

Functions:

addUser()

    Fetches random Proxmox credentials from /admin/get_random_proxmox_credentials router to assign on the user so it can have access to proxmox

    Builds and sends a POST request to /admin/create_user router to create the user on mariadb

    Validates responses and dynamically displays errors inline with form fields

token_keys()

    Collects token form data and sends a POST request to /admin/change_apikeys router which will allowed to modify the api keys and add the api secret token

    Validates backend response and displays success or failure messages

displayErrorMessage()

    Injects field-specific error messages returned by the backend into <span> tags next to each input field

### js/loginscript.js

Used only by login.html.

Binds logic to the login form on DOM load

Captures token ID and secret (for now)

Sends credentials via POST /login using fetch() 

Login is the only way to have access to webapp and depending on the privegies to adminpage

Checks response and performs manual redirection (based on returned redirect path to "/" homepage)

Handles cookie-based login (credentials: 'include') for session handling

### js/scripts.js

This is the global JS file, included across most pages via layout_homepage.html.

    Attaches DOMContentLoaded listener for when the VM form is active

    Dynamically collects form data and submits JSON to the backend endpoint

    Updates the UI with backend response statuses (success, errors, etc.)

    Includes toggleOptionalFields() to clean up form UX and show/hide advanced options


## 🧠 Why static/ is Essential

Without the static/ folder:

 - The application would have no styling, breaking UX/UI

 - Be unable to perform dynamic form submissions to create VMs, manage users or change token credentials

 - Fail to deliver a coherent user interface

 - Lose core branding elements like the logo and styling themes

This folder enables di6tpp to function like a modern web application — clean, fast, and interactive.