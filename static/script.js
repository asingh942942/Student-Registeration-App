"use strict";

const addClass = document.querySelectorAll(".add-class-btn");
const removeClass = document.querySelectorAll(".remove-class-btn");
const checkClass = document.querySelectorAll(".check-class-btn");

function AddClass() {
  fetch("/index", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ dataset: this.dataset.id, action: "add" }),
  })
    .then((response) => response.json())
    .catch((error) => {
      console.error("Error:", error);
    });
  document.location.reload();
}

function RemoveClass() {
  fetch("/index", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ dataset: this.dataset.id, action: "remove" }),
  })
    .then((response) => response.json())
    .catch((error) => {
      console.error("Error:", error);
    });
  document.location.reload();
}

function CheckClass() {
  fetch("/index", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ dataset: this.dataset.id, action: "check" }),
  })
    .then((response) => response.json())
    .then((data) => (document.location = data))
    .catch((error) => {
      console.error("Error:", error);
    });
}

addClass.forEach((button, index) => {
  button.setAttribute("data-id", index + 1);
  button.addEventListener("click", AddClass);
});

removeClass.forEach((button, index) => {
  button.setAttribute("data-id", index + 1);
  button.addEventListener("click", RemoveClass);
});

checkClass.forEach((button, index) => {
  button.setAttribute("data-id", index + 1);
  button.addEventListener("click", CheckClass);
});
