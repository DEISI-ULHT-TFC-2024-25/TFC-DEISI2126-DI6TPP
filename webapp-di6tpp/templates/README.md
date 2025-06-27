# 📁 templates/ — Frontend Layout & Dynamic Rendering

The templates/ folder defines the user interface of the DI6TPP web application using Jinja2-based HTML templates. These templates are rendered server-side by FastAPI, allowing dynamic injection of user-specific data, virtual machine (VM) configurations, and administrative control into the frontend.

Templates are modular, reusable, and cleanly separated from backend logic, supporting:

  - 🎨 Consistent visual styling across all pages

  - 🧩 Reusable layouts via Jinja2 inheritance ({% extends %} / {% block %})

  - 💡 Clear separation of presentation and logic

  - 👤 Improved user interaction and usability


## Design Approach

Templates leverage layout inheritance using {% extends %} to include base HTML structures, and {% block %} to inject specific page content:

  - Shared headers and scripts defined once (e.g., layout_homepage.html)

  - Common elements like the admin sidebar are reused (e.g., layoutAdminPage.html)

  - JavaScript and CSS are cleanly included using <link> and <script> tags

This approach avoids repetition and simplifies future UI updates.

--- 

## Page Overview

### 🔒 login.html (/login)

  Login Form page to enter the webapp which will be useful to have acess to restrict pages

  Validates input fields and displays error messages via <span> tags

  Uses its own layout and dedicated login stylesheet

---

### 🏠 index.html (/)

  Main dashboard displaying all registered VMs  

  Includes action buttons (modify/remove) per VM

  Includes a text "No VMs" if that user never created a VM

---

### 🛠️ createvm.html (/createvm)

    Comprehensive form to deploy VMs

    Includes hidden advanced fields toggled by button which makes user interaction easier

    Drop-down lists for some fields to control user input and also improves usability for the user

    Supports personalized configuration of:
      IP, CIDR, gateway, template, Disks, CPUs, RAM and bridge interface

    Optional volumes and storage paths

---

### ✏️ modify_vm.html (/modify_vm/vm_id)

Placeholder for VM editing capabilities (WIP)

---


## Admin Panel: adminPage/

All admin views share the layoutAdminPage.html, which contains:

Sidebar with links to:

  - User creation

  - All users

  - Token management

  - Logs (WIP)

  - Home redirection

Injected {% block content %} area for unique page content

Pages using this layout:

### create_user.html

  Allows administrators to register new user accounts

  Input fields:

  username: validated for minimum length and allowed characters

  password: validated for uppercase and alphanumeric rules

  role: select dropdown (admin/editor/viewer)

  Displays inline error messages beside each field via <span> elements to ensure that the data is in the correct format

  Connected to the addUser() function in adminscript.js which submits the form via JavaScript (static folder for more info)

### all_users.html

  Displays the title "Manage Users"

  Injects dynamic content into #userList using JavaScript

  Designed to show a list of all users fetched from the backend

  Lays the foundation for future features like edit/delete actions

### all_token_keys.html

  Renders a list of Proxmox credentials passed by the backend

  Each entry includes:

    Proxmox API user (credential info)

    A remove button linking to a deletion endpoint

    Fallback message shown if no credentials are present

    Ideal for administrators to verify and manage all token pairs

## token_keys.html

Form used to register or update Proxmox tokens. but mainly to add API secret key because that field it is not automated

Input fields include:

token_id: identifier of the Proxmox token

proxmox_user: name of the associated user

token_key: secret key (entered securely as password)

Connected to the token_keys() function via JavaScript

Each field includes inline error validation via <span> messages


## attacks/

### attacks.html

Provides a basic UI to initiate attacks between attacker and target VMs

Input fields for attacker IP, target IP, and attack type

Future improvements include dropdowns with existing VM IPs and attack presets and also a page to display all the possible attacks


### ⚠️ error_page.html 

Dynamically rendered error messages from exceptions

Displays status code and detailed description which is easier to report possible problems to the admins and also to stay everything presentable for users


## Shared Layouts

### layout_homepage.html

Used by most general user views (index, create VM, error page)

Includes:

  Header with logo and user greeting

  Content area defined by {% block content %}

  Linked CSS: /static/css/style.css

  JS: /static/js/scripts.js

### layoutAdminPage.html

Used by all admin dashboard templates

Features:

  Sidebar menu with navigation links

  Clean content area for each admin action

  CSS: /static/css/admin_style.css

  JS: /static/js/adminscript.js


## Why templates/ folder Matters

  - Brings interactivity and visual structure to the application

  - Allows backend-driven rendering using Jinja2 templating engine

  - Enables clean separation of backend logic and UI concerns

  - Supports multilingual and dynamic content injection

  - Easily extended with new views and layouts