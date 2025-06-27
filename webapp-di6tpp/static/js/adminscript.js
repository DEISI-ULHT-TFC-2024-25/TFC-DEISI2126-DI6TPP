// garantes that the user list is loaded when the page is fully loaded
//document.addEventListener("DOMContentLoaded", addUser);
async function addUser() {
    // Clear previous error messages
    document.querySelectorAll(".error-message").forEach(el => el.textContent = "");

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const proxmoxUser = document.getElementById("proxmox_user").value;
    const proxmox_cred_Id = document.getElementById("token_id").value;
    const proxmoxSecret = document.getElementById("token_key").value;
    const role = document.getElementById("role").value;

    try {

        const promoxData = {proxmox_cred_Id, proxmoxUser, proxmoxSecret};
        const proxmoxRes = await fetch("/admin/addcredential", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(promoxData)
        });

        const proxmoxDataResponse = await proxmoxRes.json();

        if (!proxmoxRes.ok) {
            throw proxmoxDataResponse;
        }
        const proxmoxID = proxmoxDataResponse;  

        const userData = { username, password, role, proxmox_credentials_id:proxmoxID};

        const response = await fetch("/admin/create_user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(userData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw data;
        }

        alert("User created with success: " + data.username);
        console.log("User created:", data);
        await new Promise(r => setTimeout(r, 1500));
        window.location.href = "/admin/all_users"; 
        
    } catch (error) {
        console.error("Error creating user:", error);

        if (error.detail && Array.isArray(error.detail)) {
            error.detail.forEach(displayErrorMessage);
        } else {
            if (error.detail) {
                alert("Error creating user: " + error.detail);
            } else {
                alert("Error creating user: " + (error.message || JSON.stringify(error)));
            }
        }
    }
}
async function deleteUser(user_id) {
    if (!confirm("Are you sure you want to delete this user?")) {
        return; // cancel if the user selects on "No"
    }
    fetch("/admin/all_users/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user_id })//send as a Json object
    })
    .then(async response => {
        
        const data = await response.json();
        console.log("remove function data:",data);
        
        if (!response.ok) {
            throw data;
        }
        alert("user removed with sucess: " + user_id);
        window.location.reload(); // Reload the page to reflect changes
    })
    .catch(error => {
        console.error("Error changing api keys", error);
        if (error.detail && Array.isArray(error.detail)) {
            error.detail.forEach(err => {
                displayErrorMessage(err);
            });
        }
    });
}

async function deleteToken(proxmox_id) {
    if (!confirm("Are you sure you want to delete this credential?")) {
        return; // cancel if the user selects on "No"
    }

    fetch("/admin/all_tokens_key/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proxmox_id: proxmox_id })//send as a Json object
    })
    .then(async response => {
        
        const data = await response.json();
        console.log("remove function data:",data);
        
        if (!response.ok) {
            throw data;
        }
        alert("api keys removed with sucess: " + proxmox_id);
        window.location.reload(); // Reload the page to reflect changes
    })
    .catch(error => {
        console.error("Error changing api keys", error);
        if (error.detail && Array.isArray(error.detail)) {
            error.detail.forEach(err => {
                displayErrorMessage(err);
            });
        }
    });
}

async function change_user() {
    // Clear previous error messages
    document.querySelectorAll(".error-message").forEach(el => el.textContent = "");

    // Get form values
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const proxmoxUser = document.getElementById("proxmox_user").value;
    const proxmox_cred_Id = document.getElementById("token_id").value;
    const proxmoxSecret = document.getElementById("token_key").value;
    const user_id = document.getElementById("user_id").value;

    const promoxData = {proxmox_cred_Id, proxmoxUser, proxmoxSecret};
        const proxmoxRes = await fetch("/admin/addcredential", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(promoxData)
        });

    const proxmoxID = await proxmoxRes.json();

    // Create JSON object
    const apiKeysData = {
        user_id: user_id,
        username: username,
        password: password,
        role: role,
        proxmox_credentials_id: proxmoxID,
    };
    console.log("Sending user modification request:", apiKeysData);

    fetch("/admin/all_users/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(apiKeysData)
    })
    .then(async response => {
        
        const data = await response.json();
        console.log("data:",data);
        
        if (!response.ok) {
            throw data;
        }
        alert("user changed with success: " + data.username);
        await new Promise(r => setTimeout(r, 1500));
        window.location.href = "/admin/all_users"; // Redirect to the users page after a short delay
    })
    .catch(error => {
        console.error("Error changing user", error);
        if (error.detail && Array.isArray(error.detail)) {
            error.detail.forEach(err => {
                displayErrorMessage(err);
            });
        }
    });
}


async function token_keys() {
    // Clear previous error messages
    document.querySelectorAll(".error-message").forEach(el => el.textContent = "");

    // Get form values
    const token_id = document.getElementById("token_id").value;
    const proxmox_user = document.getElementById("proxmox_user").value;
    const token_key = document.getElementById("token_key").value;
    const proxmox_id = document.getElementById("proxmox_id").value;
    console.log("Proxmox credentials ID received:", proxmox_id);

    // Create JSON object
    const apiKeysData = {
        proxmox_id: proxmox_id,
        token_id: token_id,
        proxmox_user: proxmox_user,
        token_key: token_key,
    };
    console.log("Sending token change request:", apiKeysData);

    fetch("/admin/all_tokens_key/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(apiKeysData)
    })
    .then(async response => {
        
        const data = await response.json();
        console.log("data:",data);
        
        if (!response.ok) {
            throw data;
        }
        alert("api keys changed with sucess: " + data.proxmox_user);
        await new Promise(r => setTimeout(r, 1500));
        window.location.href = "/admin/all_tokens_key";
    })
    .catch(error => {
        console.error("Error changing api keys", error);
        if (error.detail && Array.isArray(error.detail)) {
            error.detail.forEach(err => {
                displayErrorMessage(err);
            });
        }
    });
}


// Function to display error messages inside <span> elements
function displayErrorMessage(error) {
    const { loc, msg } = error;
    if (!loc || loc.length < 1) return;

    let fieldName = loc[0];
    if (loc[0] === "body" && loc.length > 1) {
        fieldName = loc[1];
    }

    const errorSpan = document.getElementById(`error-${fieldName}`);

    if (errorSpan) {
        errorSpan.textContent = msg;
        errorSpan.style.color = "red";
        errorSpan.style.fontSize = "12px";
    }
}

