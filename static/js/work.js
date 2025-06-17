document.getElementById('summaryForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    let summaryLength = document.getElementById('summaryLength').value;
    document.getElementById('summaryOutput').innerText = `Generating a ${summaryLength} summary...`;
});
