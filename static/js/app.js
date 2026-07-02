
// PREPELIGIBLE SUITE - CLIENT APPLICATION ENGINE
// Application State
let currentUser = null;
let studentProfile = null;
let companiesList = [];
let applicationsList = [];
let allStudents = [];
let allApplications = [];
let currentFilterCategory = 'all';

// On Page Load
document.addEventListener('DOMContentLoaded', () => {
    // Set Current Date
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('current-date').innerText = new Date().toLocaleDateString('en-US', options);

    // Initial session check
    checkSession();
});


// REST API CLIENT WRAPPER (Fetch utilities)
async function apiRequest(url, options = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    options.headers = {
        ...defaultHeaders,
        ...options.headers
    };

    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Something went wrong');
        }
        
        return data;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}


// SESSION & AUTHENTICATION HANDLERS
async function checkSession() {
    try {
        const data = await apiRequest('/api/auth/session');
        if (data.authenticated) {
            setupUserSession(data.user);
        } else {
            showAuthScreen();
        }
    } catch (e) {
        showAuthScreen();
    }
}

function setupUserSession(user) {
    currentUser = user;
    
    // Hide auth, show portal
    document.getElementById('auth-section').classList.remove('active-section');
    document.getElementById('portal-container').classList.add('active-portal');
    
    // Set Sidebar User Details
    document.getElementById('sidebar-username').innerText = user.name;
    document.getElementById('sidebar-role').innerText = user.role === 'admin' ? 'TPO Admin' : 'Student';
    document.getElementById('sidebar-avatar').innerText = user.name.charAt(0).toUpperCase();

    // Toggle Nav menu items and badges
    const studentElements = document.querySelectorAll('.student-nav-only');
    const adminElements = document.querySelectorAll('.admin-nav-only');
    const roleTogglePill = document.getElementById('role-toggle-pill');

    if (user.role === 'admin') {
        studentElements.forEach(el => el.style.display = 'none');
        adminElements.forEach(el => el.style.display = 'flex');
        roleTogglePill.style.display = 'block';
        roleTogglePill.querySelector('#role-badge').innerText = 'TPO ADMIN MODE';
        roleTogglePill.querySelector('#role-badge').className = 'badge badge-indigo';
        
        showView('admin-dashboard');
    } else {
        studentElements.forEach(el => el.style.display = 'flex');
        adminElements.forEach(el => el.style.display = 'none');
        roleTogglePill.style.display = 'none';
        
        // Load student data & show job board
        loadStudentProfile();
        showView('job-board');
    }
}

function showAuthScreen() {
    currentUser = null;
    studentProfile = null;
    document.getElementById('portal-container').classList.remove('active-portal');
    document.getElementById('auth-section').classList.add('active-section');
}

function switchAuthTab(tab) {
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('login-form');
    const formRegister = document.getElementById('register-form');

    if (tab === 'login') {
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        formLogin.classList.add('active');
        formRegister.classList.remove('active');
    } else {
        tabLogin.classList.remove('active');
        tabRegister.classList.add('active');
        formLogin.classList.remove('active');
        formRegister.classList.add('active');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await apiRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (response.success) {
            showToast(`Welcome back, ${response.user.name || 'User'}!`, 'success');
            setupUserSession(response.user);
        }
    } catch (e) {
        // Error toast triggered by apiRequest
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const regData = {
        email: document.getElementById('reg-email').value,
        password: document.getElementById('reg-password').value,
        name: document.getElementById('reg-name').value,
        roll_no: document.getElementById('reg-roll').value,
        branch: document.getElementById('reg-branch').value,
        cgpa: document.getElementById('reg-cgpa').value,
        tenth_percent: document.getElementById('reg-tenth').value,
        twelfth_percent: document.getElementById('reg-twelfth').value,
        active_backlogs: document.getElementById('reg-backlogs').value,
        history_backlogs: document.getElementById('reg-history').value,
        graduation_year: document.getElementById('reg-year').value,
        skills: document.getElementById('reg-skills').value,
        resume_link: document.getElementById('reg-resume').value
    };

    try {
        const response = await apiRequest('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(regData)
        });
        
        if (response.success) {
            showToast('Registration successful! Please login.', 'success');
            switchAuthTab('login');
            // Populate email input for ease
            document.getElementById('login-email').value = regData.email;
            document.getElementById('login-password').value = '';
        }
    } catch (e) {}
}

async function handleLogout() {
    try {
        const response = await apiRequest('/api/auth/logout', { method: 'POST' });
        if (response.success) {
            showToast('Logged out successfully.', 'info');
            showAuthScreen();
        }
    } catch (e) {
        showAuthScreen();
    }
}

// VIEW SWITCHER ROUTER
function showView(viewId) {
    // 1. Hide all views and remove active state from nav
    const views = document.querySelectorAll('.portal-view');
    views.forEach(view => view.classList.remove('active-view'));

    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));

    // 2. Activate target view
    const targetView = document.getElementById(`view-${viewId}`);
    if (targetView) {
        targetView.classList.add('active-view');
    }

    // 3. Highlight Nav Item
    const targetNav = document.getElementById(`nav-${viewId}`);
    if (targetNav) {
        targetNav.classList.add('active');
    }

    // 4. Update Header Title
    let viewTitleText = 'Portal';
    switch (viewId) {
        case 'job-board': viewTitleText = 'Job Opportunities & Eligibility'; loadJobBoard(); break;
        case 'student-profile': viewTitleText = 'Academic Profile & Metrics'; loadStudentProfile(); break;
        case 'student-apps': viewTitleText = 'My Job Applications'; loadStudentApplications(); break;
        case 'admin-dashboard': viewTitleText = 'TPO Analytics Overview'; loadAdminDashboard(); break;
        case 'admin-students': viewTitleText = 'Student Registry'; loadAdminStudentRegistry(); break;
        case 'admin-companies': viewTitleText = 'Company Criteria Manager'; loadAdminCompanyCriteria(); break;
        case 'admin-apps': viewTitleText = 'Review Student Applications'; loadAdminApplications(); break;
    }
    document.getElementById('view-title').innerText = viewTitleText;
}

// TOAST NOTIFICATIONS WIDGET
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-circle-xmark';
    if (type === 'info') iconClass = 'fa-circle-info';
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <div class="toast-body">${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Trigger animation slide in
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Remove toast after 3.5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3500);
}

// STUDENT LOGIC: JOB BOARD & ELIGIBILITY RADAR
async function loadJobBoard() {
    try {
        const companies = await apiRequest('/api/companies');
        companiesList = companies;
        renderJobBoard(companies);
    } catch (e) {}
}

function renderJobBoard(companies) {
    const grid = document.getElementById('companies-list-grid');
    grid.innerHTML = '';
    
    if (companies.length === 0) {
        grid.innerHTML = `
            <div class="glass-panel full-width-field" style="padding: 40px; text-align: center; grid-column: 1/-1;">
                <i class="fa-regular fa-folder-open" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 15px;"></i>
                <p style="color: var(--text-secondary)">No recruitment postings available at this time.</p>
            </div>
        `;
        return;
    }

    companies.forEach(company => {
        // Determine eligibility badge
        let elBadge = '';
        let isEligible = false;
        
        if (company.eligibility) {
            isEligible = company.eligibility.eligible;
            if (isEligible) {
                elBadge = `<span class="badge badge-green"><i class="fa-solid fa-circle-check"></i> Eligible</span>`;
            } else {
                elBadge = `<span class="badge badge-red"><i class="fa-solid fa-circle-xmark"></i> Ineligible</span>`;
            }
        }
        
        // Determine application button status
        let actionBtn = '';
        if (company.applied_status) {
            const statusLabel = company.applied_status.toUpperCase();
            let badgeClass = 'badge-indigo';
            if (statusLabel === 'SELECTED') badgeClass = 'badge-green';
            if (statusLabel === 'REJECTED') badgeClass = 'badge-red';
            if (statusLabel === 'SHORTLISTED') badgeClass = 'badge-cyan';
            
            actionBtn = `<span class="badge ${badgeClass}" style="padding: 10px; width: 100%; text-align: center; justify-content: center; font-size: 0.85rem;"><i class="fa-solid fa-file-invoice"></i> Applied: ${statusLabel}</span>`;
        } else {
            actionBtn = `
                <button class="btn btn-outline btn-sm" onclick="showCriteriaDetails(${company.id})">
                    <i class="fa-solid fa-chart-bar"></i>
                    <span>Check Eligibility</span>
                </button>
            `;
        }

        const card = document.createElement('div');
        card.className = 'company-card glass-panel';
        card.style.setProperty('--logo-color', company.logo_color);
        
        card.innerHTML = `
            <div class="card-top">
                <div class="company-logo-avatar">${company.name.charAt(0)}</div>
                <div class="company-title-block">
                    <h3>${company.name}</h3>
                    <p>${company.role}</p>
                </div>
                <div>${elBadge}</div>
            </div>
            
            <div class="card-middle">
                <div class="salary-package">
                    <i class="fa-solid fa-money-bill-wave"></i>
                    <span>${company.package}</span>
                </div>
                <div class="criteria-summary">
                    <div class="criteria-summary-row">
                        <span>Min CGPA:</span>
                        <strong>${company.min_cgpa.toFixed(2)}</strong>
                    </div>
                    <div class="criteria-summary-row">
                        <span>Branches:</span>
                        <strong style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;" title="${company.allowed_branches}">
                            ${company.allowed_branches}
                        </strong>
                    </div>
                    <div class="criteria-summary-row">
                        <span>Max Backlogs:</span>
                        <strong>${company.max_backlogs}</strong>
                    </div>
                </div>
            </div>
            
            <div class="card-bottom">
                <div class="card-status-row">
                    <span class="deadline-text"><i class="fa-regular fa-clock"></i> Deadline: ${company.deadline}</span>
                </div>
                ${actionBtn}
            </div>
        `;
        
        grid.appendChild(card);
    });
}

function filterJobs(category) {
    currentFilterCategory = category;
    
    // Update button styling
    document.getElementById('filter-all').classList.remove('active');
    document.getElementById('filter-eligible').classList.remove('active');
    document.getElementById('filter-applied').classList.remove('active');
    
    document.getElementById(`filter-${category}`).classList.add('active');
    
    filterJobBoard();
}

function filterJobBoard() {
    const searchVal = document.getElementById('job-search').value.toLowerCase();
    
    let filtered = companiesList.filter(company => {
        const matchesSearch = company.name.toLowerCase().includes(searchVal) || 
                              company.role.toLowerCase().includes(searchVal);
                              
        if (!matchesSearch) return false;
        
        if (currentFilterCategory === 'eligible') {
            return company.eligibility && company.eligibility.eligible;
        } else if (currentFilterCategory === 'applied') {
            return company.applied_status !== null;
        }
        
        return true;
    });
    
    renderJobBoard(filtered);
}

// Modal checklist breakdown handler
function showCriteriaDetails(companyId) {
    const company = companiesList.find(c => c.id === companyId);
    if (!company) return;

    const modal = document.getElementById('criteria-modal');
    document.getElementById('modal-title').innerText = `${company.name} Criteria Evaluation`;
    
    const checklistList = document.getElementById('modal-checklist-list');
    checklistList.innerHTML = '';

    const isEligible = company.eligibility.eligible;
    const banner = document.getElementById('modal-status-banner');
    const icon = document.getElementById('modal-status-icon');
    const text = document.getElementById('modal-status-text');

    if (isEligible) {
        banner.className = 'eligibility-status-banner status-eligible';
        icon.className = 'fa-solid fa-circle-check';
        text.innerText = 'YOU ARE ELIGIBLE TO APPLY!';
    } else {
        banner.className = 'eligibility-status-banner status-ineligible';
        icon.className = 'fa-solid fa-circle-xmark';
        text.innerText = 'YOU DO NOT MEET THE ELIGIBILITY CRITERIA';
    }

    // Build academic items matching checklist
    const criteriaItems = [
        {
            name: 'Academic CGPA limit',
            current: `Your CGPA: ${studentProfile.cgpa.toFixed(2)}`,
            required: `Min Required: ${company.min_cgpa.toFixed(2)}`,
            pass: studentProfile.cgpa >= company.min_cgpa
        },
        {
            name: '10th Class Percentage limit',
            current: `Your Score: ${studentProfile.tenth_percent.toFixed(1)}%`,
            required: `Min Required: ${company.min_tenth.toFixed(1)}%`,
            pass: studentProfile.tenth_percent >= company.min_tenth
        },
        {
            name: '12th Class Percentage limit',
            current: `Your Score: ${studentProfile.twelfth_percent.toFixed(1)}%`,
            required: `Min Required: ${company.min_twelfth.toFixed(1)}%`,
            pass: studentProfile.twelfth_percent >= company.min_twelfth
        },
        {
            name: 'Active Backlog limit',
            current: `Your Backlogs: ${studentProfile.active_backlogs}`,
            required: `Max Allowed: ${company.max_backlogs}`,
            pass: studentProfile.active_backlogs <= company.max_backlogs
        }
    ];

    // Branch matching check
    const allowedBranchesStr = company.allowed_branches;
    let branchPass = true;
    if (allowedBranchesStr.lower() !== 'all') {
        const allowed = allowedBranchesStr.split(',').map(b => b.trim().toLowerCase());
        branchPass = allowed.includes(studentProfile.branch.trim().toLowerCase());
    }
    criteriaItems.push({
        name: 'Eligible Specialization/Branch',
        current: `Your Branch: ${studentProfile.branch}`,
        required: `Allowed: ${company.allowed_branches}`,
        pass: branchPass
    });

    // Populate UI
    criteriaItems.forEach(item => {
        const li = document.createElement('li');
        li.className = `checklist-item ${item.pass ? 'item-pass' : 'item-fail'}`;
        
        const itemIcon = item.pass ? '<i class="fa-solid fa-circle-check"></i>' : '<i class="fa-solid fa-triangle-exclamation"></i>';
        
        li.innerHTML = `
            ${itemIcon}
            <div style="flex:1;">
                <div style="font-weight:600;">${item.name}</div>
                <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">
                    ${item.current} &bull; ${item.required}
                </div>
            </div>
            <span class="badge ${item.pass ? 'badge-green' : 'badge-red'}">${item.pass ? 'PASS' : 'FAIL'}</span>
        `;
        checklistList.appendChild(li);
    });

    // Modal footer actions
    const footerActions = document.getElementById('modal-footer-actions');
    footerActions.innerHTML = '';
    
    if (isEligible) {
        footerActions.innerHTML = `
            <button class="btn btn-outline" onclick="closeCriteriaModal()" style="margin-right:10px;">Close</button>
            <button class="btn btn-primary btn-glow" onclick="openApplyForm(${company.id})">
                <i class="fa-solid fa-paper-plane"></i>
                <span>Apply Now</span>
            </button>
        `;
    } else {
        footerActions.innerHTML = `
            <button class="btn btn-primary btn-glow" onclick="closeCriteriaModal()">Close</button>
        `;
    }

    modal.classList.add('active-modal');
}

function closeCriteriaModal() {
    document.getElementById('criteria-modal').classList.remove('active-modal');
}

function openApplyForm(companyId) {
    const company = companiesList.find(c => c.id === companyId);
    if (!company) return;
    
    closeCriteriaModal();
    
    // Fill application form fields
    document.getElementById('apply-company-id').value = company.id;
    document.getElementById('apply-modal-title').innerText = `Apply to ${company.name}`;
    document.getElementById('apply-student-name').innerText = studentProfile.name;
    document.getElementById('apply-student-roll').innerText = studentProfile.roll_no;
    document.getElementById('apply-student-branch').innerText = studentProfile.branch;
    document.getElementById('apply-student-cgpa').innerText = studentProfile.cgpa.toFixed(2);
    
    // Reset inputs
    document.getElementById('apply-location').value = '';
    document.getElementById('apply-sop').value = '';
    
    document.getElementById('apply-form-modal').classList.add('active-modal');
}

function closeApplyModal() {
    document.getElementById('apply-form-modal').classList.remove('active-modal');
}

async function submitJobApplication(event) {
    event.preventDefault();
    const companyId = document.getElementById('apply-company-id').value;
    const location = document.getElementById('apply-location').value;
    const coverLetter = document.getElementById('apply-sop').value;
    
    closeApplyModal();
    
    try {
        const response = await apiRequest('/api/applications/apply', {
            method: 'POST',
            body: JSON.stringify({
                company_id: companyId,
                preferred_location: location,
                cover_letter: coverLetter
            })
        });
        
        if (response.success) {
            showToast('Job application submitted successfully!', 'success');
            loadJobBoard();
        }
    } catch (e) {}
}

// STUDENT PROFILE WIDGET HANDLERS
async function loadStudentProfile() {
    try {
        const data = await apiRequest('/api/students/profile');
        studentProfile = data;
        
        // Fill profile overview fields
        document.getElementById('summary-name').innerText = data.name;
        document.getElementById('summary-email').innerText = currentUser.email;
        document.getElementById('summary-roll').innerText = data.roll_no;
        document.getElementById('summary-cgpa').innerText = data.cgpa.toFixed(2);
        document.getElementById('summary-marks').innerText = `${data.tenth_percent.toFixed(1)}% / ${data.twelfth_percent.toFixed(1)}%`;
        document.getElementById('summary-branch').innerText = data.branch;
        
        const backlogEl = document.getElementById('summary-backlogs');
        backlogEl.innerText = data.active_backlogs;
        backlogEl.className = data.active_backlogs > 0 ? 'val text-danger' : 'val';
        
        document.getElementById('summary-avatar-big').innerText = data.name.charAt(0).toUpperCase();

        // Render skill tags
        const tagsBox = document.getElementById('summary-skills-tags');
        tagsBox.innerHTML = '';
        if (data.skills && data.skills.trim()) {
            data.skills.split(',').forEach(skill => {
                const span = document.createElement('span');
                span.className = 'skill-tag';
                span.innerText = skill.trim();
                tagsBox.appendChild(span);
            });
        } else {
            tagsBox.innerHTML = '<span style="color:var(--text-muted); font-size:0.8rem;">No skills listed.</span>';
        }

        // Fill form fields for editing
        document.getElementById('prof-name').value = data.name;
        document.getElementById('prof-branch').value = data.branch;
        document.getElementById('prof-roll').value = data.roll_no;
        document.getElementById('prof-cgpa').value = data.cgpa;
        document.getElementById('prof-tenth').value = data.tenth_percent;
        document.getElementById('prof-twelfth').value = data.twelfth_percent;
        document.getElementById('prof-backlogs').value = data.active_backlogs;
        document.getElementById('prof-history').value = data.history_backlogs;
        document.getElementById('prof-year').value = data.graduation_year;
        document.getElementById('prof-skills').value = data.skills || '';
        document.getElementById('prof-resume').value = data.resume_link || '';

    } catch (e) {}
}

async function handleProfileUpdate(event) {
    event.preventDefault();
    
    const profileData = {
        name: document.getElementById('prof-name').value,
        branch: document.getElementById('prof-branch').value,
        cgpa: document.getElementById('prof-cgpa').value,
        tenth_percent: document.getElementById('prof-tenth').value,
        twelfth_percent: document.getElementById('prof-twelfth').value,
        active_backlogs: document.getElementById('prof-backlogs').value,
        history_backlogs: document.getElementById('prof-history').value,
        graduation_year: document.getElementById('prof-year').value,
        skills: document.getElementById('prof-skills').value,
        resume_link: document.getElementById('prof-resume').value
    };

    try {
        const response = await apiRequest('/api/students/profile', {
            method: 'POST',
            body: JSON.stringify(profileData)
        });
        
        if (response.success) {
            showToast('Academic metrics updated successfully!', 'success');
            loadStudentProfile();
        }
    } catch (e) {}
}

async function loadStudentApplications() {
    try {
        const apps = await apiRequest('/api/applications/student');
        const tbody = document.getElementById('student-apps-tbody');
        tbody.innerHTML = '';
        
        if (apps.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 30px; color: var(--text-muted)">
                        You haven't submitted any job applications yet.
                    </td>
                </tr>
            `;
            return;
        }

        apps.forEach(app => {
            const dateStr = new Date(app.applied_at).toLocaleDateString('en-US', {
                year: 'numeric', month: 'short', day: 'numeric'
            });

            // Status label selection
            const statusLabel = app.status.toUpperCase();
            let badgeClass = 'badge-indigo';
            if (statusLabel === 'SELECTED') badgeClass = 'badge-green';
            if (statusLabel === 'REJECTED') badgeClass = 'badge-red';
            if (statusLabel === 'SHORTLISTED') badgeClass = 'badge-cyan';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${app.company_name}</strong></td>
                <td>${app.role}</td>
                <td><span class="font-cyan" style="font-weight:700">${app.package}</span></td>
                <td>${dateStr}</td>
                <td><span class="badge ${badgeClass}">${statusLabel}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {}
}

// ==========================================================================
// ADMIN / TPO OPERATIONS
// ==========================================================================
async function loadAdminDashboard() {
    try {
        const data = await apiRequest('/api/admin/dashboard-stats');
        
        // Fill KPI counts
        document.getElementById('stat-total-students').innerText = data.stats.total_students;
        document.getElementById('stat-total-companies').innerText = data.stats.total_companies;
        document.getElementById('stat-total-apps').innerText = data.stats.total_applications;
        document.getElementById('stat-placement-rate').innerText = `${data.stats.placement_rate}%`;

        // Render Graph widths
        const total = data.stats.total_applications || 1;
        const statusMap = data.status_breakdown;
        
        document.getElementById('val-selected').innerText = statusMap.Selected;
        document.getElementById('bar-selected').style.width = `${(statusMap.Selected / total) * 100}%`;
        
        document.getElementById('val-shortlisted').innerText = statusMap.Shortlisted;
        document.getElementById('bar-shortlisted').style.width = `${(statusMap.Shortlisted / total) * 100}%`;

        document.getElementById('val-applied').innerText = statusMap.Applied;
        document.getElementById('bar-applied').style.width = `${(statusMap.Applied / total) * 100}%`;

        document.getElementById('val-rejected').innerText = statusMap.Rejected;
        document.getElementById('bar-rejected').style.width = `${(statusMap.Rejected / total) * 100}%`;

        // Render Branch details table
        const branchTbody = document.getElementById('admin-branch-stats-tbody');
        branchTbody.innerHTML = '';
        
        if (data.branch_stats.length === 0) {
            branchTbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align:center; padding:15px; color:var(--text-muted)">No registered departments.</td>
                </tr>
            `;
            return;
        }

        data.branch_stats.forEach(branch => {
            const totalStudents = branch.total;
            const placed = branch.placed;
            const successRate = totalStudents > 0 ? ((placed / totalStudents) * 100).toFixed(1) : '0.0';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${branch.branch}</strong></td>
                <td>${totalStudents}</td>
                <td><span class="text-success">${placed} Placed</span></td>
                <td><span class="badge badge-indigo">${successRate}%</span></td>
            `;
            branchTbody.appendChild(tr);
        });

    } catch (e) {}
}

async function loadAdminStudentRegistry() {
    try {
        const students = await apiRequest('/api/admin/students');
        allStudents = students;
        renderRegistryTable(students);
    } catch (e) {}
}

function renderRegistryTable(students) {
    const tbody = document.getElementById('admin-students-tbody');
    tbody.innerHTML = '';
    
    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 30px; color: var(--text-muted)">
                    No student records found.
                </td>
            </tr>
        `;
        return;
    }

    students.forEach(student => {
        const resumeBtn = student.resume_link ? 
            `<a href="${student.resume_link}" target="_blank" class="resume-cell-link"><i class="fa-solid fa-arrow-up-right-from-square"></i> View</a>` : 
            `<span style="color:var(--text-muted)">None</span>`;

        const skillsStr = student.skills ? 
            student.skills.split(',').slice(0, 3).map(s => s.trim()).join(', ') + (student.skills.split(',').length > 3 ? '...' : '') :
            'None';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div style="font-weight:600;">${student.name}</div>
                <div style="font-size:0.75rem; color:var(--text-secondary);">${student.email}</div>
            </td>
            <td><span class="badge badge-indigo">${student.roll_no}</span></td>
            <td>${student.branch}</td>
            <td><strong class="font-cyan">${student.cgpa.toFixed(2)}</strong></td>
            <td>${student.tenth_percent.toFixed(1)}% / ${student.twelfth_percent.toFixed(1)}%</td>
            <td>
                <span class="${student.active_backlogs > 0 ? 'text-danger' : 'text-success'}" style="font-weight:600">
                    ${student.active_backlogs}
                </span>
            </td>
            <td title="${student.skills || ''}">${skillsStr}</td>
            <td>${resumeBtn}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterRegistry() {
    const searchVal = document.getElementById('student-search').value.toLowerCase();
    const branchVal = document.getElementById('student-filter-branch').value;

    let filtered = allStudents.filter(student => {
        const matchesSearch = student.name.toLowerCase().includes(searchVal) || 
                              student.roll_no.toLowerCase().includes(searchVal);
                              
        const matchesBranch = (branchVal === 'All' || student.branch === branchVal);

        return matchesSearch && matchesBranch;
    });

    renderRegistryTable(filtered);
}

// Admin Company criteria listing
async function loadAdminCompanyCriteria() {
    try {
        const companies = await apiRequest('/api/companies');
        const listContainer = document.getElementById('admin-companies-list');
        listContainer.innerHTML = '';

        if (companies.length === 0) {
            listContainer.innerHTML = `<p style="text-align:center; color:var(--text-muted); margin-top:40px;">No companies currently active.</p>`;
            return;
        }

        companies.forEach(company => {
            const item = document.createElement('div');
            item.className = 'admin-posting-item';
            item.style.setProperty('--logo-color', company.logo_color);
            
            item.innerHTML = `
                <div class="posting-info-block">
                    <h4>${company.name} &mdash; <span class="font-cyan">${company.role}</span></h4>
                    <p style="margin-top:2px;">CGPA &ge; ${company.min_cgpa.toFixed(2)} &bull; Backlogs &le; ${company.max_backlogs} &bull; Package: ${company.package}</p>
                    <p style="font-size:0.75rem; margin-top:2px; color:var(--text-muted);"><i class="fa-regular fa-clock"></i> Deadline: ${company.deadline}</p>
                </div>
                <div class="posting-actions">
                    <button class="btn btn-outline btn-danger btn-sm" onclick="handleDeleteCompany(${company.id})">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            `;
            listContainer.appendChild(item);
        });

    } catch (e) {}
}

async function handleAddCompany(event) {
    event.preventDefault();

    const companyData = {
        name: document.getElementById('comp-name').value,
        role: document.getElementById('comp-role').value,
        package: document.getElementById('comp-package').value,
        min_cgpa: document.getElementById('comp-cgpa').value,
        min_tenth: document.getElementById('comp-tenth').value,
        min_twelfth: document.getElementById('comp-twelfth').value,
        max_backlogs: document.getElementById('comp-backlogs').value,
        allowed_branches: document.getElementById('comp-branches').value,
        deadline: document.getElementById('comp-deadline').value,
        logo_color: document.getElementById('comp-color').value
    };

    try {
        const response = await apiRequest('/api/admin/companies', {
            method: 'POST',
            body: JSON.stringify(companyData)
        });

        if (response.success) {
            showToast('Recruitment details posted successfully!', 'success');
            document.getElementById('add-company-form').reset();
            // Default color reset helper
            document.getElementById('comp-color').value = '#4f46e5';
            document.getElementById('comp-branches').value = 'All';
            loadAdminCompanyCriteria();
        }
    } catch (e) {}
}

async function handleDeleteCompany(id) {
    if (!confirm('Are you sure you want to delete this company placement opportunity? This action is permanent and deletes all student submissions.')) return;

    try {
        const response = await apiRequest(`/api/admin/companies/${id}`, {
            method: 'DELETE'
        });

        if (response.success) {
            showToast('Opportunity removed successfully.', 'success');
            loadAdminCompanyCriteria();
        }
    } catch (e) {}
}

// Admin Applications Review
async function loadAdminApplications() {
    try {
        const apps = await apiRequest('/api/admin/applications');
        allApplications = apps;
        renderAdminAppsTable(apps);
    } catch (e) {}
}

function renderAdminAppsTable(apps) {
    const tbody = document.getElementById('admin-apps-tbody');
    tbody.innerHTML = '';

    if (apps.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 30px; color: var(--text-muted)">
                    No applications submitted yet.
                </td>
            </tr>
        `;
        return;
    }

    apps.forEach(app => {
        const appliedDate = new Date(app.applied_at).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        });

        // Resume Link helper
        const resumeBtn = app.resume_link ? 
            `<a href="${app.resume_link}" target="_blank" class="resume-cell-link"><i class="fa-solid fa-file-pdf"></i> Resume</a>` : 
            `<span style="color:var(--text-muted)">None</span>`;

        // Badge Status selector
        const statusLabel = app.status.toUpperCase();
        let badgeClass = 'badge-indigo';
        if (statusLabel === 'SELECTED') badgeClass = 'badge-green';
        if (statusLabel === 'REJECTED') badgeClass = 'badge-red';
        if (statusLabel === 'SHORTLISTED') badgeClass = 'badge-cyan';

        // Action controls
        let actionControls = '';
        if (app.status === 'Applied') {
            actionControls = `
                <div style="display:flex; gap:6px;">
                    <button class="btn btn-success btn-sm" onclick="updateApplicationStatus(${app.application_id}, 'Shortlisted')" title="Shortlist Student">
                        <i class="fa-solid fa-list-check"></i>
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="updateApplicationStatus(${app.application_id}, 'Rejected')" title="Reject Application">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            `;
        } else if (app.status === 'Shortlisted') {
            actionControls = `
                <div style="display:flex; gap:6px;">
                    <button class="btn btn-success btn-sm" onclick="updateApplicationStatus(${app.application_id}, 'Selected')" title="Select/Place Student">
                        <i class="fa-solid fa-user-check"></i> Placed
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="updateApplicationStatus(${app.application_id}, 'Rejected')" title="Reject Application">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            `;
        } else {
            actionControls = `<span style="font-size:0.8rem; color:var(--text-muted);">Decided</span>`;
        }

        const truncatedSop = app.cover_letter ? 
            (app.cover_letter.length > 50 ? app.cover_letter.substring(0, 47) + '...' : app.cover_letter) : 
            'No Statement of Purpose submitted.';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${app.student_name}</strong></td>
            <td><span class="badge badge-indigo">${app.roll_no}</span></td>
            <td>
                <div style="font-size:0.85rem;">CGPA: <strong>${app.cgpa.toFixed(2)}</strong></div>
                <div style="font-size:0.75rem; color:var(--text-secondary);">${app.branch}</div>
            </td>
            <td>
                <div style="font-weight:600;">${app.company_name}</div>
                <div style="font-size:0.75rem; color:var(--text-secondary);">${app.company_role}</div>
            </td>
            <td>${resumeBtn}</td>
            <td>
                <div style="font-size:0.85rem; font-weight:600;"><i class="fa-solid fa-location-dot" style="color:var(--accent-cyan); font-size:0.75rem; margin-right:4px;"></i>${app.preferred_location || 'Not Specified'}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${app.cover_letter || ''}">
                    SOP: ${truncatedSop}
                </div>
            </td>
            <td>${appliedDate}</td>
            <td><span class="badge ${badgeClass}">${statusLabel}</span></td>
            <td>${actionControls}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function updateApplicationStatus(appId, status) {
    try {
        const response = await apiRequest(`/api/admin/applications/${appId}`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });

        if (response.success) {
            showToast(`Application status updated to ${status}.`, 'success');
            loadAdminApplications();
        }
    } catch (e) {}
}

function filterAdminApps() {
    const searchVal = document.getElementById('app-search').value.toLowerCase();
    const statusVal = document.getElementById('app-filter-status').value;

    let filtered = allApplications.filter(app => {
        const matchesSearch = app.student_name.toLowerCase().includes(searchVal) || 
                              app.company_name.toLowerCase().includes(searchVal) ||
                              app.roll_no.toLowerCase().includes(searchVal);
                              
        const matchesStatus = (statusVal === 'All' || app.status === statusVal);

        return matchesSearch && matchesStatus;
    });

    renderAdminAppsTable(filtered);
}
