const gaTrackingCode = 'UA-125778965-6';

function disablePerformanceGroup() {
    // disable google analytics
    window[`ga-disable-${gaTrackingCode}`] = true;
  }
  
  function handleOneTrustCookieGroups(oneTrustCookie) {
    const STRICTLY_NECESSARY_GROUP_ID = "C0001";
    const PERFORMANCE_GROUP_ID = "C0002";
    const FUNCTIONAL_GROUP_ID = "C0003";
    const ADVERTISING_GROUP_ID = "C0004";
    const SOCIAL_MEDIA_GROUP_ID = "C0005";
  
    const splitCookieValue = oneTrustCookie.split('=');
    const cookieValues = new URLSearchParams(splitCookieValue.slice(1).join('='));
    const cookieGroups = cookieValues.get('groups');
    const disabledCookieGroups = cookieGroups && cookieGroups.split(',')
      .map(cookie => cookie.split(':'))
      .filter(([groupName, enabled]) => enabled == 0);
  
    disabledCookieGroups && disabledCookieGroups.forEach(([group]) => {
      if (group === PERFORMANCE_GROUP_ID) {
        disablePerformanceGroup();
      }
    });
  }
  
  function findOneTrustCookie() {
    const oneTrustCookie = document.cookie
      .split(';')
      .map(cookie => cookie.trim())
      .find(cookie => {
        const [cookieName] = cookie.split('=');
        return cookieName === 'OptanonConsent';
      });
  
    return oneTrustCookie;
  }
  
  function OptanonWrapper() {
    const oneTrustCookie = findOneTrustCookie();
    if (oneTrustCookie) {
      handleOneTrustCookieGroups(oneTrustCookie);
    }
  }
