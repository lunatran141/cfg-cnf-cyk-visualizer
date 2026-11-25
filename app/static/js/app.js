"use strict";

/**
 * Dữ liệu ví dụ dùng để minh họa giao diện.
 * Thuật toán xử lý thật sẽ được tích hợp ở các task sau.
 */
const exampleData = {
    grammar: [
        "S -> AB | BC",
        "A -> BA | a",
        "B -> CC | b",
        "C -> AB | a",
    ].join("\n"),
    startSymbol: "S",
    word: "baaba",
};

/**
 * Lấy các phần tử cần sử dụng trên giao diện.
 */
const grammarForm = document.querySelector("#grammar-form");
const grammarInput = document.querySelector("#grammar-input");
const startSymbolInput = document.querySelector(
    "#start-symbol-input",
);
const wordInput = document.querySelector("#word-input");

const loadExampleButton = document.querySelector(
    "#load-example-button",
);
const resetButton = document.querySelector("#reset-button");

const emptyResult = document.querySelector("#empty-result");
const resultContent = document.querySelector("#result-content");
const resultStatus = document.querySelector("#result-status");

const grammarOutput = document.querySelector("#grammar-output");
const wordOutput = document.querySelector("#word-output");


/**
 * Đưa khu vực kết quả về trạng thái chờ dữ liệu.
 */
function showWaitingState() {
    emptyResult.hidden = false;
    resultContent.hidden = true;

    resultStatus.textContent = "Đang chờ dữ liệu";
    resultStatus.classList.remove("ready");
    resultStatus.classList.add("waiting");

    grammarOutput.textContent = "";
    wordOutput.textContent = "";
}


/**
 * Hiển thị dữ liệu vừa được người dùng nhập.
 *
 * Đây mới là chức năng minh họa của skeleton T01.
 * Parser CFG và thuật toán CYK chưa được gọi ở bước này.
 */
function showInputPreview(grammar, startSymbol, word) {
    emptyResult.hidden = true;
    resultContent.hidden = false;

    resultStatus.textContent = "Đã nhận dữ liệu";
    resultStatus.classList.remove("waiting");
    resultStatus.classList.add("ready");

    grammarOutput.textContent = [
        `Ký hiệu bắt đầu: ${startSymbol}`,
        "",
        grammar,
    ].join("\n");

    wordOutput.textContent = word;
}


/**
 * Điền dữ liệu CFG mẫu vào form.
 */
function loadExample() {
    grammarInput.value = exampleData.grammar;
    startSymbolInput.value = exampleData.startSymbol;
    wordInput.value = exampleData.word;

    grammarInput.focus();
}


/**
 * Xử lý sự kiện gửi form.
 */
function handleSubmit(event) {
    event.preventDefault();

    const grammar = grammarInput.value.trim();
    const startSymbol = startSymbolInput.value.trim();
    const word = wordInput.value.trim();

    if (!grammar || !startSymbol || !word) {
        return;
    }

    showInputPreview(grammar, startSymbol, word);
}


/**
 * Xử lý sau khi trình duyệt reset form.
 */
function handleReset() {
    window.setTimeout(() => {
        showWaitingState();
        grammarInput.focus();
    }, 0);
}


loadExampleButton.addEventListener("click", loadExample);
grammarForm.addEventListener("submit", handleSubmit);
resetButton.addEventListener("click", handleReset);

showWaitingState();