let regist = document.querySelectorAll('.tab-pane'),
    button = document.querySelectorAll('.fw-semibold'),
    item = document.querySelectorAll(".item"),
    index = document.querySelectorAll('.index')

index.forEach((i, number) => {
    i.addEventListener('click', () => {
        index.forEach(p => {
            p.classList.remove("active")
        })
        i.classList.add("active")
        item.forEach(t => {
            t.classList.remove('work')
        })
        item[number].classList.add("work")
    })
})

button.forEach((i, index) => {
    i.addEventListener('click', () => {
        button.forEach(t => {
            t.classList.remove('active')
        })
        i.classList.add('active')
        regist.forEach(p => {
            p.classList.remove('active', 'show')
        })
        regist[index].classList.add('active', 'show')
    })
})
const changePasswordBtn = document.getElementById("change-password-btn");
if (changePasswordBtn) {
    changePasswordBtn.addEventListener("click", function (e) {
        e.preventDefault();
        const passwordForm = document.getElementById("change-password-form");
        const editInfoForm = document.getElementById("edit-info-form");
        const editUserForm = document.getElementById("edit-user-form");

        passwordForm.style.display = (passwordForm.style.display === "none" || passwordForm.style.display === "") ? "block" : "none";
        editInfoForm.style.display = "none";
        editUserForm.style.display = "none";
    });
}

const editInfoBtn = document.getElementById("edit-info-btn");
if (editInfoBtn) {
    editInfoBtn.addEventListener("click", function (e) {
        e.preventDefault();
        const passwordForm = document.getElementById("change-password-form");
        const editInfoForm = document.getElementById("edit-info-form");
        const editUserForm = document.getElementById("edit-user-form");

        editInfoForm.style.display = (editInfoForm.style.display === "none" || editInfoForm.style.display === "") ? "block" : "none";
        passwordForm.style.display = "none";
        editUserForm.style.display = "none";
    });
}
const editUserBtn = document.getElementById("edit-user-btn");
if (editUserBtn) {
    editUserBtn.addEventListener("click", function (e) {
        e.preventDefault();
        const passwordForm = document.getElementById("change-password-form");
        const editInfoForm = document.getElementById("edit-info-form");
        const editUserForm = document.getElementById("edit-user-form");
        editUserForm.style.display = (editUserForm.style.display === "none" || editUserForm.style.display === "") ? "block" : "none";
        editInfoForm.style.display = "none";
        passwordForm.style.display = "none";
    });
}


const prices = document.querySelectorAll(".price");
let total = 0;
for (let i = 0; i < prices.length; i++) {
    const price = parseFloat(prices[i].innerText);

    if (!isNaN(price)) {
        total += price;
    }
}
let subtotal = total + (total * 0.10)
document.querySelector(".subtotal-value").innerText = subtotal.toFixed(2);
document.querySelector(".order-total bdi").innerText = "$" + total.toFixed(2);

