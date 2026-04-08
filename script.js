const STORAGE_KEY = "spend-trend-v2-transactions";
const THEME_KEY = "spend-trend-v2-theme";

const form = document.getElementById("transactionForm");
const titleInput = document.getElementById("title");
const amountInput = document.getElementById("amount");
const dateInput = document.getElementById("date");
const typeInput = document.getElementById("type");
const categoryInput = document.getElementById("category");
const notesInput = document.getElementById("notes");
const list = document.getElementById("transactionList");
const breakdownList = document.getElementById("breakdownList");
const totalIncomeEl = document.getElementById("totalIncome");
const totalExpenseEl = document.getElementById("totalExpense");
const balanceEl = document.getElementById("balance");
const monthlyExpenseEl = document.getElementById("monthlyExpense");
const themeToggle = document.getElementById("themeToggle");
const filterButtons = document.querySelectorAll("[data-filter]");
const chartCanvas = document.getElementById("trendChart");
const chartCtx = chartCanvas.getContext("2d");

let currentFilter = "all";
let transactions = loadTransactions();

function loadTransactions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.error("Could not read saved transactions:", error);
    return [];
  }
}

function saveTransactions() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(transactions));
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(Number(value) || 0);
}

function formatDate(value) {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(date);
}

function getFilteredTransactions() {
  if (currentFilter === "all") {
    return transactions;
  }

  return transactions.filter((transaction) => transaction.type === currentFilter);
}

function getMonthlyExpenseTotal() {
  const now = new Date();
  return transactions
    .filter((transaction) => {
      if (transaction.type !== "expense") {
        return false;
      }

      const date = new Date(`${transaction.date}T00:00:00`);
      return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
    })
    .reduce((sum, transaction) => sum + transaction.amount, 0);
}

function renderSummary() {
  const income = transactions
    .filter((transaction) => transaction.type === "income")
    .reduce((sum, transaction) => sum + transaction.amount, 0);

  const expenses = transactions
    .filter((transaction) => transaction.type === "expense")
    .reduce((sum, transaction) => sum + transaction.amount, 0);

  totalIncomeEl.textContent = formatCurrency(income);
  totalExpenseEl.textContent = formatCurrency(expenses);
  balanceEl.textContent = formatCurrency(income - expenses);
  monthlyExpenseEl.textContent = formatCurrency(getMonthlyExpenseTotal());
}

function renderList() {
  const filtered = [...getFilteredTransactions()].sort((a, b) => {
    return new Date(`${b.date}T00:00:00`) - new Date(`${a.date}T00:00:00`);
  });

  list.innerHTML = "";

  if (filtered.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "No transactions in this view yet.";
    list.appendChild(empty);
    return;
  }

  filtered.forEach((transaction) => {
    const item = document.createElement("li");
    item.className = "transaction-item";

    const main = document.createElement("div");
    main.className = "transaction-main";

    const titleRow = document.createElement("div");
    titleRow.className = "transaction-title-row";

    const title = document.createElement("p");
    title.className = "transaction-title";
    title.textContent = transaction.title;

    const tag = document.createElement("span");
    tag.className = "transaction-tag";
    tag.textContent = `${transaction.category} • ${transaction.type}`;

    const meta = document.createElement("p");
    meta.className = "transaction-meta";
    meta.textContent = formatDate(transaction.date);

    titleRow.append(title, tag);
    main.append(titleRow, meta);

    if (transaction.notes) {
      const notes = document.createElement("p");
      notes.className = "transaction-notes";
      notes.textContent = transaction.notes;
      main.appendChild(notes);
    }

    const actions = document.createElement("div");
    actions.className = "transaction-actions";

    const amount = document.createElement("strong");
    amount.className = transaction.type === "income" ? "amount-income" : "amount-expense";
    amount.textContent = `${transaction.type === "income" ? "+" : "-"}${formatCurrency(transaction.amount)}`;

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "delete-button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => {
      transactions = transactions.filter((entry) => entry.id !== transaction.id);
      saveTransactions();
      render();
    });

    actions.append(amount, deleteButton);
    item.append(main, actions);
    list.appendChild(item);
  });
}

function renderBreakdown() {
  breakdownList.innerHTML = "";

  const expenseTransactions = transactions.filter((transaction) => transaction.type === "expense");

  if (expenseTransactions.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Add expenses to see category totals.";
    breakdownList.appendChild(empty);
    return;
  }

  const totalsByCategory = expenseTransactions.reduce((accumulator, transaction) => {
    const nextValue = (accumulator[transaction.category] || 0) + transaction.amount;
    accumulator[transaction.category] = nextValue;
    return accumulator;
  }, {});

  const rows = Object.entries(totalsByCategory)
    .sort((a, b) => b[1] - a[1]);

  const maxValue = rows[0][1];

  rows.forEach(([category, total]) => {
    const item = document.createElement("div");
    item.className = "breakdown-item";

    const topLine = document.createElement("div");
    topLine.className = "breakdown-topline";

    const label = document.createElement("span");
    label.textContent = category;

    const amount = document.createElement("span");
    amount.textContent = formatCurrency(total);

    const bar = document.createElement("div");
    bar.className = "breakdown-bar";

    const fill = document.createElement("div");
    fill.className = "breakdown-fill";
    fill.style.width = `${(total / maxValue) * 100}%`;

    topLine.append(label, amount);
    bar.appendChild(fill);
    item.append(topLine, bar);
    breakdownList.appendChild(item);
  });
}

function renderChart() {
  const width = chartCanvas.width;
  const height = chartCanvas.height;
  chartCtx.clearRect(0, 0, width, height);

  const style = getComputedStyle(document.body);
  const textColor = style.getPropertyValue("--text").trim();
  const mutedColor = style.getPropertyValue("--muted").trim();
  const accentColor = style.getPropertyValue("--accent").trim();
  const borderColor = style.getPropertyValue("--border").trim();

  const today = new Date();
  const dailyTotals = [];

  for (let offset = 6; offset >= 0; offset -= 1) {
    const day = new Date(today);
    day.setHours(0, 0, 0, 0);
    day.setDate(today.getDate() - offset);

    const isoDate = day.toISOString().slice(0, 10);
    const total = transactions
      .filter((transaction) => transaction.type === "expense" && transaction.date === isoDate)
      .reduce((sum, transaction) => sum + transaction.amount, 0);

    dailyTotals.push({
      label: day.toLocaleDateString("en-US", { weekday: "short" }),
      total
    });
  }

  const values = dailyTotals.map((entry) => entry.total);
  const maxValue = Math.max(...values, 0);

  chartCtx.lineWidth = 1;
  chartCtx.strokeStyle = borderColor;
  chartCtx.fillStyle = textColor;
  chartCtx.font = "12px sans-serif";

  if (maxValue === 0) {
    chartCtx.fillStyle = mutedColor;
    chartCtx.fillText("Add expense entries to see the last 7 days.", 24, height / 2);
    return;
  }

  const padding = { top: 24, right: 24, bottom: 40, left: 24 };
  const graphHeight = height - padding.top - padding.bottom;
  const graphWidth = width - padding.left - padding.right;
  const stepX = graphWidth / (dailyTotals.length - 1 || 1);

  chartCtx.beginPath();
  chartCtx.moveTo(padding.left, padding.top);
  chartCtx.lineTo(padding.left, height - padding.bottom);
  chartCtx.lineTo(width - padding.right, height - padding.bottom);
  chartCtx.stroke();

  chartCtx.beginPath();
  dailyTotals.forEach((entry, index) => {
    const x = padding.left + (stepX * index);
    const y = padding.top + graphHeight - ((entry.total / maxValue) * graphHeight);
    if (index === 0) {
      chartCtx.moveTo(x, y);
    } else {
      chartCtx.lineTo(x, y);
    }
  });
  chartCtx.strokeStyle = accentColor;
  chartCtx.lineWidth = 3;
  chartCtx.stroke();

  dailyTotals.forEach((entry, index) => {
    const x = padding.left + (stepX * index);
    const y = padding.top + graphHeight - ((entry.total / maxValue) * graphHeight);

    chartCtx.beginPath();
    chartCtx.fillStyle = accentColor;
    chartCtx.arc(x, y, 4.5, 0, Math.PI * 2);
    chartCtx.fill();

    chartCtx.fillStyle = mutedColor;
    chartCtx.textAlign = "center";
    chartCtx.fillText(entry.label, x, height - 14);
  });

  const lastPoint = dailyTotals[dailyTotals.length - 1];
  chartCtx.fillStyle = textColor;
  chartCtx.textAlign = "right";
  chartCtx.fillText(`Latest: ${formatCurrency(lastPoint.total)}`, width - padding.right, padding.top - 4);
}

function render() {
  renderSummary();
  renderList();
  renderBreakdown();
  renderChart();
}

function applyTheme(theme) {
  const isDark = theme === "dark";
  document.body.classList.toggle("dark", isDark);
  themeToggle.textContent = isDark ? "Light mode" : "Dark mode";
  localStorage.setItem(THEME_KEY, theme);
  renderChart();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const title = titleInput.value.trim();
  const amount = Number(amountInput.value);
  const date = dateInput.value;
  const type = typeInput.value;
  const category = categoryInput.value;
  const notes = notesInput.value.trim();

  if (!title || !Number.isFinite(amount) || amount <= 0 || !date) {
    return;
  }

  transactions.push({
    id: crypto.randomUUID(),
    title,
    amount,
    date,
    type,
    category,
    notes
  });

  saveTransactions();
  render();
  form.reset();
  dateInput.value = new Date().toISOString().slice(0, 10);
  typeInput.value = "expense";
  categoryInput.value = "Food";
});

themeToggle.addEventListener("click", () => {
  const nextTheme = document.body.classList.contains("dark") ? "light" : "dark";
  applyTheme(nextTheme);
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentFilter = button.dataset.filter || "all";
    filterButtons.forEach((chip) => chip.classList.toggle("active", chip === button));
    renderList();
  });
});

dateInput.value = new Date().toISOString().slice(0, 10);
applyTheme(localStorage.getItem(THEME_KEY) || "light");
render();
