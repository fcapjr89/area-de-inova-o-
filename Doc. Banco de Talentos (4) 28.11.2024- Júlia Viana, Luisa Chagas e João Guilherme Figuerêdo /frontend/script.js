document.addEventListener("DOMContentLoaded", function() {
    displayMembers();

    document.getElementById('search').addEventListener('input', () => {
        const searchTerm = document.getElementById('search').value.toLowerCase();
        displayMembers(member => member.name.toLowerCase().includes(searchTerm));
    });

    document.getElementById('ageFilter').addEventListener('input', applyFilters);
    document.getElementById('courseFilter').addEventListener('change', applyFilters);
    document.getElementById('skillsFilter').addEventListener('input', applyFilters);

    document.getElementById('toggleFiltersButton').addEventListener('click', () => {
        const filterContainer = document.querySelector('.filter-container');
        filterContainer.style.display = filterContainer.style.display === 'none' || filterContainer.style.display === '' ? 'flex' : 'none';
    });
});

let members = JSON.parse(localStorage.getItem('members')) || [];
let editIndex = null;

function saveToLocalStorage() {
    localStorage.setItem('members', JSON.stringify(members));
}

function createCard(member, index) {
    const card = document.createElement('div');
    card.className = 'card';

    card.innerHTML = `
        <div class="card-photo">
            ${member.photo ? `<img src="${member.photo}" alt="Foto de ${member.name}">` : 'Sem Foto'}
        </div>
        <div class="card-content">
            <div><strong>Nome:</strong> ${member.name}</div>
            <div><strong>Idade:</strong> ${member.age}</div>
            <div><strong>Habilidades:</strong> ${member.skills}</div>
            <div><strong>Experiência:</strong> ${member.experience}</div>
            <div><strong>Telefone:</strong> ${member.phone}</div>
            <div><strong>Email:</strong> ${member.email}</div>
            <div><strong>Curso:</strong> ${member.course}</div>
            <div><strong>LinkedIn:</strong> <a href="${member.linkedin}" target="_blank">${member.linkedin}</a></div>
            <div><strong>Currículo:</strong> ${member.pdf ? `<a href="${member.pdf}" download="Curriculo_${member.name}.pdf">Baixar PDF</a>` : 'Não disponível'}</div>
        </div>
        <div class="buttons">
            <button onclick="editMember(${index})">Editar</button>
            <button onclick="removeMember(${index})">Remover</button>
        </div>
    `;

    document.getElementById('cardsContainer').appendChild(card);
}

function displayMembers(filterFn = null) {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';
    members
        .filter(member => (filterFn ? filterFn(member) : true))
        .forEach((member, index) => createCard(member, index));
}

function applyFilters() {
    const ageFilter = parseInt(document.getElementById('ageFilter').value) || null;
    const courseFilter = document.getElementById('courseFilter').value.toLowerCase();
    const skillsFilter = document.getElementById('skillsFilter').value.toLowerCase();

    displayMembers(member => {
        return (!ageFilter || member.age === ageFilter) &&
               (!courseFilter || member.course.toLowerCase() === courseFilter) &&
               (!skillsFilter || member.skills.toLowerCase().includes(skillsFilter));
    });
}

function openForm() {
    const form = document.getElementById('formContainer');
    form.style.display = form.style.display === 'none' || form.style.display === '' ? 'block' : 'none';
}

function addMember() {
    const name = document.getElementById('nameInput').value;
    const age = parseInt(document.getElementById('ageInput').value);
    const skills = document.getElementById('skillsInput').value;
    const experience = document.getElementById('experienceInput').value;
    const phone = document.getElementById('phoneInput').value;
    const email = document.getElementById('emailInput').value;
    const course = document.getElementById('courseInput').value;
    const linkedin = document.getElementById('linkedinInput').value;
    const photoInput = document.getElementById('photoInput').files[0];
    const pdfInput = document.getElementById('pdfInput').files[0];

    let photoUrl = photoInput ? URL.createObjectURL(photoInput) : null;
    let pdfUrl = pdfInput ? URL.createObjectURL(pdfInput) : null;

    const newMember = { name, age, skills, experience, phone, email, course, linkedin, photo: photoUrl, pdf: pdfUrl };

    if (editIndex !== null) {
        members[editIndex] = newMember;
        editIndex = null;
    } else {
        members.push(newMember);
    }

    saveToLocalStorage();
    displayMembers();
    closeForm();
}

function editMember(index) {
    const member = members[index];
    document.getElementById('nameInput').value = member.name;
    document.getElementById('ageInput').value = member.age;
    document.getElementById('skillsInput').value = member.skills;
    document.getElementById('experienceInput').value = member.experience;
    document.getElementById('phoneInput').value = member.phone;
    document.getElementById('emailInput').value = member.email;
    document.getElementById('courseInput').value = member.course;
    document.getElementById('linkedinInput').value = member.linkedin;

    editIndex = index;
    openForm();
}

function removeMember(index) {
    members.splice(index, 1);
    saveToLocalStorage();
    displayMembers();
}

function closeForm() {
    const form = document.getElementById('formContainer');
    form.style.display = 'none';
    document.getElementById('formContainer').reset();
}
