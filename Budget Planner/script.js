(() => {
  "use strict";

  const STORAGE_KEY = "student-expense-tracker-v1";
  const PERIODS = {
    week: { budgetLabel: "Weekly budget" },
    month: { budgetLabel: "Monthly budget" },
    semester: { budgetLabel: "Semester budget" },
  };
  const CATEGORIES = new Set(["Food", "Transport", "Books", "Supplies", "Housing", "Other"]);
  const currency = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  });
  const dateFormatter = new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  const budgetForm = document.querySelector("#budget-form");
  const budgetInput = document.querySelector("#budget-amount");
  const expenseForm = document.querySelector("#expense-form");
  const expenseNameInput = document.querySelector("#expense-name");
  const expenseAmountInput = document.querySelector("#expense-amount");
  const expenseCategoryInput = document.querySelector("#expense-category");
  const expenseDateInput = document.querySelector("#expense-date");
  const periodInput = document.querySelector(".period");
  const budgetLabel = document.querySelector("#budget-label");
  const budgetSummary = document.querySelector("#budget-summary");
  const spentSummary = document.querySelector("#spent-summary");
  const remainingSummary = document.querySelector("#remaining-summary");
  const expenseHistory = document.querySelector("#expense-history");
  const status = document.querySelector("#tracker-status");

  const blankState = () => ({
    budgets: { week: 0, month: 0, semester: 0 },
    expenses: [],
    period: "month",
  });

  function isValidState(value) {
    return value !== null &&
      typeof value === "object" &&
      value.budgets !== null &&
      typeof value.budgets === "object" &&
      ["week", "month", "semester"].every((period) =>
        Number.isSafeInteger(value.budgets[period]) && value.budgets[period] >= 0
      ) &&
      Array.isArray(value.expenses) &&
      value.expenses.every((expense) =>
        expense !== null &&
        typeof expense === "object" &&
        typeof expense.id === "string" &&
        typeof expense.name === "string" &&
        Number.isSafeInteger(expense.amount) &&
        expense.amount > 0 &&
        CATEGORIES.has(expense.category) &&
        isValidDate(expense.date)
      ) &&
      Object.hasOwn(PERIODS, value.period);
  }

  function isValidDate(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return false;
    }
    const [year, month, day] = value.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    return date.getFullYear() === year &&
      date.getMonth() === month - 1 &&
      date.getDate() === day;
  }

  function showStatus(message, isError = false) {
    status.textContent = message;
    status.dataset.error = String(isError);
    status.hidden = !message;
  }

  function loadState() {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === null) {
        return blankState();
      }
      const parsed = JSON.parse(saved);
      if (!isValidState(parsed)) {
        throw new Error("Saved tracker data has an unsupported or invalid format.");
      }
      return parsed;
    } catch (error) {
      showStatus(`Could not load saved data: ${error.message}`, true);
      return blankState();
    }
  }

  let state = loadState();

  function saveState(nextState) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
      state = nextState;
      showStatus("Your changes have been saved.");
      render();
      return true;
    } catch (error) {
      showStatus(`Could not save your changes: ${error.message}`, true);
      return false;
    }
  }

  function dateKey(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function periodBounds(period, today = new Date()) {
    const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    if (period === "week") {
      start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
      const end = new Date(start);
      end.setDate(end.getDate() + 7);
      return { start: dateKey(start), end: dateKey(end) };
    }
    if (period === "month") {
      return {
        start: dateKey(new Date(today.getFullYear(), today.getMonth(), 1)),
        end: dateKey(new Date(today.getFullYear(), today.getMonth() + 1, 1)),
      };
    }
    const semesterStartMonth = today.getMonth() < 6 ? 0 : 6;
    return {
      start: dateKey(new Date(today.getFullYear(), semesterStartMonth, 1)),
      end: dateKey(new Date(today.getFullYear(), semesterStartMonth + 6, 1)),
    };
  }

  function getCurrentExpenses() {
    const { start, end } = periodBounds(state.period);
    return state.expenses.filter((expense) => expense.date >= start && expense.date < end);
  }

  function render() {
    const selectedPeriod = state.period;
    const currentPeriodExpenses = getCurrentExpenses();
    const spent = currentPeriodExpenses.reduce((total, expense) => total + expense.amount, 0);
    const budget = state.budgets[selectedPeriod];

    periodInput.value = selectedPeriod;
    budgetLabel.textContent = PERIODS[selectedPeriod].budgetLabel;
    budgetInput.value = (budget / 100).toFixed(2);
    budgetSummary.textContent = currency.format(budget / 100);
    spentSummary.textContent = currency.format(spent / 100);
    remainingSummary.textContent = currency.format((budget - spent) / 100);
    remainingSummary.classList.toggle("over-budget", spent > budget);

    expenseHistory.replaceChildren();
    state.expenses
      .slice()
      .sort((first, second) => second.date.localeCompare(first.date) || second.id.localeCompare(first.id))
      .forEach((expense) => {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        const categoryCell = document.createElement("td");
        const category = document.createElement("span");
        const dateCell = document.createElement("td");
        const amountCell = document.createElement("td");
        const actionCell = document.createElement("td");
        const deleteButton = document.createElement("button");

        nameCell.textContent = expense.name;
        category.className = "category";
        category.textContent = expense.category;
        categoryCell.append(category);
        dateCell.textContent = dateFormatter.format(new Date(`${expense.date}T00:00:00`));
        amountCell.className = "amount";
        amountCell.textContent = currency.format(expense.amount / 100);
        deleteButton.type = "button";
        deleteButton.className = "delete-button";
        deleteButton.dataset.expenseId = expense.id;
        deleteButton.setAttribute("aria-label", `Delete ${expense.name}`);
        deleteButton.textContent = "Delete";
        actionCell.append(deleteButton);
        row.append(nameCell, categoryCell, dateCell, amountCell, actionCell);
        expenseHistory.append(row);
      });

    if (state.expenses.length === 0) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.className = "empty-state";
      cell.colSpan = 5;
      cell.textContent = "No expenses recorded yet.";
      row.append(cell);
      expenseHistory.append(row);
    }
  }

  budgetForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const amount = Number(budgetInput.value);
    if (!Number.isFinite(amount) || amount < 0 || !Number.isSafeInteger(Math.round(amount * 100))) {
      showStatus("Enter a valid budget amount of zero or more.", true);
      budgetInput.focus();
      return;
    }

    const nextState = {
      ...state,
      budgets: { ...state.budgets, [state.period]: Math.round(amount * 100) },
    };
    saveState(nextState);
  });

  expenseForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const name = expenseNameInput.value.trim();
    const amount = Number(expenseAmountInput.value);
    const category = expenseCategoryInput.value;
    const date = expenseDateInput.value;

    if (!name) {
      showStatus("Enter an expense name.", true);
      expenseNameInput.focus();
      return;
    }
    if (!Number.isFinite(amount) || amount <= 0 || !Number.isSafeInteger(Math.round(amount * 100))) {
      showStatus("Enter a valid expense amount greater than zero.", true);
      expenseAmountInput.focus();
      return;
    }
    if (!CATEGORIES.has(category)) {
      showStatus("Select a valid expense category.", true);
      expenseCategoryInput.focus();
      return;
    }
    if (!isValidDate(date)) {
      showStatus("Select a valid expense date.", true);
      expenseDateInput.focus();
      return;
    }

    const expense = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      name,
      amount: Math.round(amount * 100),
      category,
      date,
    };
    if (expense.amount < 1) {
      showStatus("The expense amount must be at least one paisa.", true);
      expenseAmountInput.focus();
      return;
    }

    if (saveState({ ...state, expenses: [...state.expenses, expense] })) {
      expenseForm.reset();
      expenseDateInput.value = dateKey(new Date());
    }
  });

  expenseHistory.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-expense-id]");
    if (!button) {
      return;
    }
    const expenses = state.expenses.filter((expense) => expense.id !== button.dataset.expenseId);
    if (expenses.length !== state.expenses.length) {
      saveState({ ...state, expenses });
    }
  });

  periodInput.addEventListener("change", () => {
    saveState({ ...state, period: periodInput.value });
  });

  expenseDateInput.value = dateKey(new Date());
  render();
})();