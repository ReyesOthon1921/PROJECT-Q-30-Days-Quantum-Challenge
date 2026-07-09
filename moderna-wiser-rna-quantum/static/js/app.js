async function validateStructure() {
    const sequence = document.getElementById('sequence').value;
    const structure = document.getElementById('structure').value;
    const resultsBox = document.getElementById('results');

    resultsBox.textContent = 'Running validation...';

    try {
        const response = await fetch('/api/validate-structure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sequence: sequence,
                structure: structure
            })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = 'Frontend error: ' + error;
    }
}
