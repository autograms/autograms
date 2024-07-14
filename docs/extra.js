document.addEventListener("DOMContentLoaded", function() {

  // Check if the current page is the home page
  const pathname = window.location.pathname;


  // Specific path for the home page
  if (pathname === '/autograms' || pathname === '/autograms/') {

    document.body.classList.add('home-page');
  } 
});