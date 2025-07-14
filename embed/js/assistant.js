// assistant.js
// Used to detected when the link has been embedded into Blackboard, and what the course code is by parsing and extracting the filepath from Blackboard's CDN.
// Then, reconstructs the course/semester/class codes to build links
// NOTE: KNOW WHAT AND WHERE YOU'RE LINKING!
//  Course-Profiles lists course codes as:   CourseCode_ClassCode_SemesterCode
//       Blackboard lists course codes as:   CourseCode_SemesterCode_ClassCode

// Unified JacSON embed controller
(function () {
  const allowedDomains = [
    "learn.uq.edu.au",
    "saas-stage.learn.uq.edu.au"
  ];
  const currentHost = window.location.hostname;

  // PREVIEW INSTRUCTION ONLY
  if (allowedDomains.includes(currentHost)) {
    const preloadMessage = document.createElement("p");
    preloadMessage.className = "jacson-preload";
    preloadMessage.textContent = 'Click on the "Save" button at the top-right to finish inserting the Assessment Overview table';
    document.body.appendChild(preloadMessage);
    return; // Stop further execution
  }

  // PRODUCTION BEHAVIOUR (CDN delivery with full functionality)
  document.addEventListener('DOMContentLoaded', () => {
    const url = window.location.href;
    const fullSpan   = document.getElementById('fullCourseCode');   // e.g. "BSAN7209_7560_60200"
    const courseSpan = document.getElementById('CourseCode');       // e.g. "BSAN7209"
    const semSpan    = document.getElementById('SemesterCode');     // e.g. "7560"
    const classSpan  = document.getElementById('ClassCode');        // e.g. "60200"
    const iframe     = document.getElementById('jacsonFrame');
    const profileLink = document.getElementById("profileLink");
    const fallbackLink = document.getElementById("fallbackLink");

    const match = url.match(/\/courses\/([^\/]+)\//);
    if (!match) {
      const msg = 'Click on the save button and refresh page. If you still get this message, then course code not detected. (ERROR)';
      fullSpan && (fullSpan.textContent = msg);
      courseSpan && (courseSpan.textContent = '');
      semSpan && (semSpan.textContent = '');
      classSpan && (classSpan.textContent = '');
      return;
    }

    const fullCourseCode = match[1];  // e.g. "BSAN7209_7560_60200"
    const [courseCode, semesterCode, classCode] = fullCourseCode.split('_');
    const jsonPath = `/jacson/profiles/${semesterCode}/${courseCode}-${classCode}-${semesterCode}`;
    const newSrc = `https://uqgblaze.github.io/jacson/embed/assessment-table.html?json=${jsonPath}`;

    fullSpan && (fullSpan.textContent = fullCourseCode);
    courseSpan && (courseSpan.textContent = courseCode);
    semSpan && (semSpan.textContent = semesterCode);
    classSpan && (classSpan.textContent = classCode);
    iframe && (iframe.src = newSrc);

    const fallbackURL = `https://programs-courses.uq.edu.au/course.html?course_code=${courseCode}`;
    if (fallbackLink) {
      fallbackLink.href = fallbackURL;
      fallbackLink.textContent = fallbackURL;
    }
    if (courseCode && classCode && semesterCode && profileLink) {
      profileLink.href = `https://course-profiles.uq.edu.au/course-profiles/${courseCode}-${classCode}-${semesterCode}`;
    } else if (profileLink) {
      profileLink.href = fallbackURL;
    }
  });
})();
