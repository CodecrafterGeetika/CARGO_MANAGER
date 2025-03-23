document.addEventListener("DOMContentLoaded", function () {
    fetchCargoData();
});

function fetchCargoData() {
    fetch("http://127.0.0.1:8000/api/items")
        .then(response => response.json())
        .then(data => {
            const cargoTable = document.getElementById("cargoTable");
            cargoTable.innerHTML = "";
            data.data.forEach(item => {
                const row = `<tr>
                    <td>${item.itemId}</td>
                    <td>${item.name}</td>
                    <td>${item.preferredZone || 'N/A'}</td>
                    <td>${item.priority}</td>
                    <td>${item.status}</td>
                </tr>`;
                cargoTable.innerHTML += row;
            });
        })
        .catch(error => console.error("Error fetching cargo:", error));
}