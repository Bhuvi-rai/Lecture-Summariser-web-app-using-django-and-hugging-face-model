document.getElementById("quizForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const result = document.getElementById("result");
    const q1 = document.querySelector('input[name="q1"]:checked');

    if (!q1) {
        result.innerHTML = "<p>Please answer the question before submitting.</p>";
        result.style.color = "red";
    } else {
        const answer = q1.value;
        if (answer === "4") {
            result.innerHTML = "<p>Correct! 2 + 2 = 4</p>";
            result.style.color = "green";
        } else {
            result.innerHTML = "<p>Incorrect. Try again!</p>";
            result.style.color = "red";
        }
    }
});
