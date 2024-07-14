function checkHomePage() {
  // Check if the current page is the home page
  const pathname = window.location.pathname;

  // Specific path for the home page
  if (pathname === '/autograms' || pathname === '/autograms/' || pathname === '/autograms/index.html') {

    document.body.classList.add('home-page');
  } 
  
}

document.addEventListener("DOMContentLoaded", function() {

  checkHomePage();
});

window.addEventListener("pageshow", function(event) {

  checkHomePage();
});