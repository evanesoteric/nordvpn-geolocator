// Select table 
const table = document.getElementById('vpns');

// Initial data params
let vpnData = []; 
let nextIndex = 0;

// Fetch initial data batch immediately on page load
fetchData(nextIndex);

// Handle infinite scroll
window.addEventListener('scroll', () => {
  const { scrollTop, clientHeight, scrollHeight } = document.documentElement;

  if(scrollTop + clientHeight >= scrollHeight - 5) {
    fetchData(nextIndex);
  }
});

// Fetch and display data 
function fetchData(offset) {
  fetch(`/api/vpns?limit=10&offset=${offset}`)
    .then(res => res.json())
    .then(data => {
      // Append to vpnData  
      vpnData.push(...data);

      // Display rows  
      displayVPNs(data);

      // Update offset for next batch  
      nextIndex = vpnData.length;
    })
    .catch(error => {
      console.error("Error in fetch:", error);
    });
}

function displayVPNs(vpns) {
  vpns.forEach(vpn => {
    const row = `
        <tr>
          <td>${vpn.name}</td>
          <td>${vpn.ip}</td>
          <td>${vpn.city}</td>
          <td>${vpn.state}</td>   
          <td>${vpn.type}</td>  
        </tr>`;

    table.querySelector('tbody').insertAdjacentHTML('beforeend', row);
  });
}
