console.log(" scripts.js loaded!");

function showStatus(message) {
    let statusDiv = document.getElementById("status-message");
    
    if (!statusDiv) {
        statusDiv = document.createElement("div");
        statusDiv.id = "status-message";
         statusDiv.className = "status-box";
        document.body.appendChild(statusDiv);
    }

    statusDiv.textContent = message;
}

function fetchWithTimeout(url, options = {}, timeout = 600000) { // 600000 = 10 min
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Request timed out")), timeout)
        )
    ]);
}

function displayErrorMessage(err) {
    // loc is an array and will extract all the locs that exists
    const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : err.loc;
    const message = err.msg;

    // search for span with id error `error-field` from html
    const span = document.getElementById(`error-${field}`);

    if (span) {
        span.textContent = message;
    } else {
        console.warn(`⚠️ Span not found in the field: ${field}`);
        showStatus(`Error in "${field}": ${message}`);
    }
}

//this function is used to send/start the request to the endpoint provided
async function sendStepRequest(endpoint, data) {
    //delete all previous error messages
    document.querySelectorAll(".error-message").forEach(span => {
        span.textContent = "";
    });

    let response;

    try {
        response = await fetchWithTimeout(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }, 600000); // 10 minutes so we have enought time to run the package script
    
    } catch (err) {
        console.error(`❌ Network or Timeout error on ${endpoint}`, err);
        showStatus(`❌ Timeout or network error on ${endpoint}`);
        return { success: false };
    }

    if (!response) {
        showStatus(`❌ No response received from ${endpoint}`);
        return { success: false };
    }
    
    if (!response.ok) {
    // small and simple error without much detail from starting the task
    showStatus(`❌ Server error on ${endpoint}: ${response.status}`);
    return { success: false };
    }

  let jsonResponse;
  try {
    jsonResponse = await response.json();
  } catch (err) {
    console.error(`❌ Failed to parse JSON from ${endpoint}`, err);
    showStatus(`❌ Invalid JSON from ${endpoint}`);
    return { success: false };
  }

  console.log(`✅ Response from ${endpoint}:`, jsonResponse);

  // to criation task endpoints, only retriving task_id
  if (!jsonResponse.task_id) {
    showStatus(`❌ Missing task_id in response from ${endpoint}`);
    return { success: false };
  }

  return { success: true, data: jsonResponse };
}

async function waitUntilTaskIsFinished(taskId, maxAttempts, interval) {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    console.log(`Waiting for task ${taskId}... ${maxAttempts - attempts} attempts left.`);
    const res = await fetch(`/task-status/${taskId}`);
    const data = await res.json();

    if (data.status === "success") return { success: true };
    if (data.status === "error") return { success: false, error: data.error };

    await new Promise(r => setTimeout(r, interval));
    attempts++;
  }
  throw new Error("⏱️ Timeout: task didn't finish in the expected time.");   
}


async function handleVmFormSubmit(formElement) {
    document.querySelectorAll(".error-message").forEach(span => {
        span.textContent = "";
    });
    document.getElementById("status-message")?.remove();

    let formData = new FormData(formElement);  
    let jsonObject = {};
    formData.forEach((value, key) => {
        jsonObject[key] = value;
    });

    console.log("Sending data:", jsonObject);
    alert("Start creating VM. Check the process on bottom of the page.");
    try {
        // 0. sending to /update_vms
        const updateResp = await sendStepRequest("/update_vms", jsonObject);
        console.log("updateResp:", updateResp.data);
        if (!updateResp.success) return;

        const updateTaskId = updateResp.data.task_id;
        const updateStatus = await waitUntilTaskIsFinished(updateTaskId, 30, 6000);
        if (!updateStatus.success) throw new Error(updateStatus.error || "Task failed.");

        // 1. sending to /create-vm-entry. this sucess it means backend accepted the request, 
        // add with sucess the task but is still running the code
        const updateRespCreate = await sendStepRequest("/create-vm-entry", jsonObject);
        console.log("updateRespCreate:", updateRespCreate);
        //this will tell that the task was created
        if (!updateRespCreate.success) return;

        const updateTaskIdCreate = updateRespCreate.data.task_id;
        showStatus("waiting for Saving VM data on Mariadb...");
        // this will retrive the task with it's details, task_id and the sucess which means the task is finished
        const updateStatusCreate = await waitUntilTaskIsFinished(updateTaskIdCreate,5, 6000);
        if (!updateStatusCreate.success) {
            // Aqui mostramos o erro no formulário
            if (Array.isArray(updateStatusCreate.error)) {
                // Se for uma lista de erros pydantic, mostramos cada um
                updateStatusCreate.error.forEach(err => displayErrorMessage(err));
            } else {
                // Caso contrário, mostramos erro geral
                alert(updateStatusCreate.error || "Task failed.");
            }
            return;  // Para não continuar
        }

        // 2. sending to /generate_vm on create_vm file
        const updateRespGenerate = await sendStepRequest("/generate_vm", jsonObject);
        if (!updateRespGenerate.success) return;

        const updateTaskIdGenerate= updateRespGenerate.data.task_id;
        showStatus("📦 Generate Terraform and applying...");
        const updateStatusGenerate = await waitUntilTaskIsFinished(updateTaskIdGenerate, 10, 5000);
        if (!updateStatusGenerate.success) throw new Error(updateStatus.error || "Task failed.");


        // 3. sending to /configure-vm
        const updateRespConfigure = await sendStepRequest("/configure-vm", jsonObject);
        if (!updateRespConfigure.success) return;

        const updateTaskIdConfigure= updateRespConfigure.data.task_id;
        showStatus("🔧 Instaling the needed packages on VM... It will take a while!");
        const updateStatusConfigure = await waitUntilTaskIsFinished(updateTaskIdConfigure, 50, 10000);
        if (!updateStatusConfigure.success) return;


        showStatus("✅ VM created successfully!");
        //so the user can see the status message
        await new Promise(r => setTimeout(r, 1500));
        window.location.href = "/"; //redirect to the main page after 100ms so the user can see the status message
    } catch (error) {
        console.error("❌ Error found while sending the form:", error);
        alert("Error processing the request. Check logs for more info.");
    }
}

function toggleOptionalFields() {
    //get the id
    let optionalFields = document.getElementById("optionalFields");
    //wait for when the button is clicked
    let button = document.querySelector("button[onclick='toggleOptionalFields()']");
    
    //verify is the style of optionalFields is none 
    if (optionalFields.style.display === "none") {
        optionalFields.style.display = "block";
        button.textContent = "More ▲";
    } else {
        optionalFields.style.display = "none";
        button.textContent = "Hide ▼";
    }
}

function updateDiskValue(val) {
    document.getElementById('vmdisk01Number').value = val;
}

function updateSliderValue(val) {
    document.getElementById('vmdisk01Slider').value = val;
}


async function deleteVm(vm_id) {
    if (!confirm("Are you sure you want to delete this vm?")) {
        return; // cancel if the user selects on "No"
    }
    console.log("Deleting vm with ID:", vm_id);
    fetch("/delete-vm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vm_id: vm_id })//send as a Json object
    })
    .then(async response => {
        const text = await response.text();
        
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error("Failed to parse JSON:", e);
            throw new Error("Invalid JSON response from server.");
        }
        
        if (!response.ok) {
            throw data;
        }
        alert("vm_id removed with success: " + vm_id);
        window.location.reload(); // Reload the page to reflect changes
    })
    .catch(error => {
        console.error("Error deleting vm", error);
        if (error.detail && Array.isArray(error.detail)) {
            error.detail.forEach(err => {
                displayErrorMessage(err);
            });
        }
    });
}


document.addEventListener("DOMContentLoaded", function() {
    console.log("📜 DOM totally loaded!");

    // Attach handler para create VM
    const vmCreateForm = document.getElementById("vmCreateForm");
    if (vmCreateForm) {
        console.log(" vmCreateForm found inside of DOMContentLoaded!");
        console.log("vmCreateForm found - attaching submit handler.");
        vmCreateForm.addEventListener("submit", async function(event) {
            event.preventDefault();
            event.target.disabled = true;// Disable the form to prevent multiple submissions
            console.log("handleVmFormSubmit");
            await handleVmFormSubmit(this);
            event.target.disabled = false; // Re-enable the form after submission
        });

    } else {
        console.log(" vmCreateForm not found inside of DOMContentLoaded!");
    }
});