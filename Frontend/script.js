import { initializeApp } from "firebase/app";
import { getFirestore, collection, addDoc, getDocs, deleteDoc, doc, updateDoc } from "firebase/firestore";

// Configuração do Firebase
const firebaseConfig = {
    apiKey: "SUA_API_KEY",
    authDomain: "SEU_AUTH_DOMAIN",
    projectId: "SEU_PROJECT_ID",
    storageBucket: "SEU_STORAGE_BUCKET",
    messagingSenderId: "SEU_MESSAGING_SENDER_ID",
    appId: "SEU_APP_ID"
};


const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const profilesCollection = collection(db, "profiles");

let editIndex = null; // Para controlar edições

document.addEventListener("DOMContentLoaded", () => {
    console.log("Documento carregado");
    displayMembers();

    document.getElementById("search").addEventListener("input", () => {
        const searchTerm = document.getElementById("search").value.toLowerCase();
        displayMembers(member => member.name.toLowerCase().includes(searchTerm));
    });

    document.getElementById("toggleFiltersButton").addEventListener("click", () => {
        const filterContainer = document.querySelector(".filter-container");
        filterContainer.style.display = filterContainer.style.display === "none" || filterContainer.style.display === "" ? "flex" : "none";
    });

    document.getElementById("submitMemberButton").addEventListener("click", addMember);
    document.getElementById("cancelFormButton").addEventListener("click", closeForm);
    document.getElementById("addButton").addEventListener("click", openForm);

    // Filtros
    document.getElementById("ageFilter").addEventListener("input", applyFilters);
    document.getElementById("courseFilter").addEventListener("change", applyFilters);
    document.getElementById("skillsFilter").addEventListener("input", applyFilters);
});

async function displayMembers(filterFn = null) {
    const container = document.getElementById("cardsContainer");
    container.innerHTML = ""; // Limpa os cards existentes

    try {
        const querySnapshot = await getDocs(profilesCollection);
        const members = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        members.filter(filterFn || (() => true)).forEach(createCard);
    } catch (error) {
        console.error("Erro ao carregar membros:", error);
    }
}

function createCard(member) {
    const card = document.createElement("div");
    card.className = "card";

    card.innerHTML = `
        <div class="card-photo">
            ${member.photo ? `<img src="${member.photo}" alt="Foto de ${member.name}">` : "Sem Foto"}
        </div>
        <div class="card-content">
            <div><strong>Nome:</strong> ${member.name}</div>
            <div><strong>Idade:</strong> ${member.age}</div>
            <div><strong>Habilidades:</strong> ${member.skills}</div>
            <div><strong>Curso:</strong> ${member.course}</div>
        </div>
        <div class="buttons">
            <button onclick="editMember('${member.id}')">Editar</button>
            <button onclick="removeMember('${member.id}')">Remover</button>
        </div>
    `;

    const container = document.getElementById("cardsContainer");
    container.appendChild(card);
}

async function addMember() {
    const name = document.getElementById("nameInput").value;
    const age = parseInt(document.getElementById("ageInput").value);
    const skills = document.getElementById("skillsInput").value;
    const course = document.getElementById("courseInput").value;

    if (!name || !age || !skills || !course) {
        alert("Preencha todos os campos obrigatórios.");
        return;
    }

    const newMember = { name, age, skills, course };

    try {
        if (editIndex) {
            const memberDoc = doc(db, "profiles", editIndex);
            await updateDoc(memberDoc, newMember);
            editIndex = null;
        } else {
            await addDoc(profilesCollection, newMember);
        }
        displayMembers();
        closeForm();
    } catch (error) {
        console.error("Erro ao salvar membro:", error);
    }
}

async function editMember(id) {
    try {
        const memberDoc = doc(db, "profiles", id);
        const docSnapshot = await getDoc(memberDoc);
        const member = docSnapshot.data();

        document.getElementById("nameInput").value = member.name;
        document.getElementById("ageInput").value = member.age;
        document.getElementById("skillsInput").value = member.skills;
        document.getElementById("courseInput").value = member.course;

        editIndex = id;
        openForm();
    } catch (error) {
        console.error("Erro ao carregar membro para edição:", error);
    }
}

async function removeMember(id) {
    try {
        const memberDoc = doc(db, "profiles", id);
        await deleteDoc(memberDoc);
        displayMembers();
    } catch (error) {
        console.error("Erro ao remover membro:", error);
    }
}

function openForm() {
    document.getElementById("formContainer").style.display = "block";
}

function closeForm() {
    document.getElementById("formContainer").style.display = "none";
    document.querySelectorAll(".form-container input, .form-container textarea").forEach(input => input.value = "");
}

function applyFilters() {
    const ageFilter = parseInt(document.getElementById("ageFilter").value) || null;
    const courseFilter = document.getElementById("courseFilter").value.toLowerCase();
    const skillsFilter = document.getElementById("skillsFilter").value.toLowerCase();

    displayMembers(member => {
        return (!ageFilter || member.age === ageFilter) &&
               (!courseFilter || member.course.toLowerCase() === courseFilter) &&
               (!skillsFilter || member.skills.toLowerCase().includes(skillsFilter));
    });
}

window.openForm = openForm;
window.closeForm = closeForm;
window.addMember = addMember;
window.editMember = editMember;
window.removeMember = removeMember;
