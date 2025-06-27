

document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM fully loaded in login page- initializing form handlers");

    // Handler for Login Form (only attach if form exists)
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        console.log("login-form found - attaching submit handler.");
        loginForm.addEventListener("submit", async function(event) {
            event.preventDefault();
            alert("Submitting login form...");
            try {
                const username = document.getElementById("username").value;
                const password = document.getElementById("password").value;

                const jsonObject = { username, password };
                console.log("📤 JSON sent (login):", jsonObject);
                
                //i choose fetch because allows to controle more (tokens,messages) better than traditional form
                const response = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    credentials: "include", //to store the cookie on the request
                    body: JSON.stringify(jsonObject)
                });

                const jsonResponse = await response.json();

                console.log("status code", jsonResponse);
                if (response.status === 401) return alert(jsonResponse.message || "Invalid credentials! Try Another One");
                if (!response.ok) return alert(json.detail || "Unknown error during login");
                
            
                console.log("JSON received (login):", jsonResponse);

                //goes to the body response "redirect:" especifict and see where we want to redirect
                //fetch doesnt have redirect integrated
                if (jsonResponse.redirect) {
                    window.location.href = jsonResponse.redirect;
                } else {
                    alert(jsonResponse.message || "Login successful!");
                }

            } catch (error) {
                console.error("Error during login:", error);
                alert("Login failed. Please check your credentials.");
            }
        });
    } else {
        console.log(" login-form not found - skipping login handler.");
    }
});

 
async function logout(username,password) {

    try {
        const jsonObject = { username, password };
        
        console.log("User logging out:", jsonObject);

        response = await fetch("/admin/logout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(jsonObject)
        });

        const data = await response.json();

        if (!response.ok) {
            throw data;
        }

        console.log("User logged out:", data);

    } catch (error) {
        console.error("Error logging out:", error);

        if (error.detail && Array.isArray(error.detail)) {
            error.detail.forEach(displayErrorMessage);
        } else {
            alert("Error logging out: " + (error.message || JSON.stringify(error)));
        }
    }
}