var initTour = new Tour({
	 	name: "Starters tour",
	 	debug:true,
		backdrop: true,
		basePath: '/idm/',
    template: "<div class='popover tour'>\
    <div class='arrow'></div>\
    <h3 class='popover-title'></h3>\
    <div class='popover-content'></div>\
    <div class='popover-navigation'><div class='btn-group'>\
        <button class='btn btn-default' data-role='prev' onclick='initTour.prev()'>« Prev</button>\
        <button class='btn btn-default' data-role='next' onclick='initTour.next()'>Next »</button>\
    </div>\
        <button class='btn btn-default' data-role='end' onclick='initTour.end()'>End tour</button>\
    </div>",
	  steps: [
			{
				title: "Let's get started!",
				content: "Welcome to the FIWARE's keyrock IdM. This is a basic tour through the main features",
				orphan: true
			},
			{
				title: "FIWARE Portal",
				content: "The FIWARE's IdM is part of FIWARE Lab. You an check the other FIWARE lab components in this bar.",
				orphan: true
			},
			{
				element: "#applications",
				title: "Applications", 
				content: "This is the applications table",
				placement: "right"
			},
			{
				element: "#organizations",
				title: "Organizations", 
				content: "This is this the organizations table",
				placement: "left"
			}, 
			{
				title: "Initial tour finished!",
				content: "You have finished the basic tour. Click in the button to start learning to register your applications or click 'End tour' to exit the tour",
				orphan: true
      },
		]
});

function startInitTour(){
	window.localStorage.clear();
	initTour.init();
	initTour.start(true);
}

function startAppTour(){
	initTour.end();
	appTour.init();
	appTour.start(true);
} 

var appTour = new Tour({ 
	 	name: "Applications tour",
		backdrop: true,
		debug:true,
    onEnd: function (tour) {
      window.localStorage.clear();
    }
	});

$( document ).ready(function() {
	var orgTour = new Tour({ 
	 	name: "Organizations tour",
		backdrop: true,
		debug:true,
    onEnd: function (tour) {
      window.localStorage.clear();
    }
	});

	var rolesTour = new Tour({ 
	 	name: "Roles and permissions tour",
		backdrop: true,
		debug:true,
    onEnd: function (tour) {
      window.localStorage.clear();
    }
	});

	var adminTour = new Tour({ 
	 	name: "Account features tour",
		backdrop: true,
		debug:true,
    onEnd: function (tour) {
      window.localStorage.clear();
    }
	});
	

	appTour.addSteps([
	{
      element: "#applications__action_register_application",
      title: "Register an application", 
      content: "Click here to start registering an application",
      path:"/idm/",
      placement: "right"
    },	
    {
      title: "Register an application", 
      content: "Fill this form to create an application",
      path:"/idm/myApplications/create/",
      orphan: true
    },
    {
      element: "#id_name",
      title: "Register an application", 
      content: "This is the name",
      path:"/idm/myApplications/create/",
      placement: "left",
      onShow: function (appTour) {
          $("#id_name").val("FIWARE Wonder APP");
      }
    },
    {
      element: "#id_description",
      title: "Register an application", 
      content: "This is the description",
      path:"/idm/myApplications/create/",
      placement: "left",
      onShow: function (appTour) {
          $("#id_description").val("Some description of the app.");
      }
    },
    {
      element: "#id_url",
      title: "Register an application", 
      content: "This is the url of your app",
      path:"/idm/myApplications/create/",
      placement: "left",
      onShow: function (appTour) {
          $("#id_url").val("myappurl.com");
      }
    },
    {
      element: "#id_callbackurl",
      title: "Register an application", 
      content: "This is the callbackurl of your app.",
      path:"/idm/myApplications/create/",
      placement: "left",
      onShow: function (appTour) {
          $("#id_callbackurl").val("myappurl.com/callback");
      },
      onNext: function (appTour) {
        $(".btn-primary").click();
      }
    }
 ]);
/*
  orgTour.addSteps([
    {
      element: "#applications__action_register_organization",
      title: "Register an organization", 
      content: "You must click in this link to start resgistering your organization",
      placement: "left",
      path:"/idm/"
    },
    {
      element: "#id_name",
      title: "Register an organization", 
      content: "This is the name",
      path:"/idm/organizations/create/",
      placement: "left",
      onShow: function (orgTour) {
          $("#id_name").val("Fancy organization");
      }
    },
    {
      element: "#id_description",
      title: "Register an organization", 
      content: "This is the description",
      path:"/idm/organizations/create/",
      placement: "left",
      onShow: function (orgTour) {
          $("#id_description").val("Some description of the organization.");
      },
      onNext: function (appTour) {
        $(".btn-primary").click();
      }
    },
    {
      title: "Your organization has been created", 
      content: "This is the main page of your brand new organization",
      path:"/idm/home_orgs/"
    },
    {
      element: "#applications",
      title: "Organization main page", 
      content: "This table displays the apps related to your organization",
      path:"/idm/home_orgs/"
    },
    {
      element: "#members",
      title: "Organization main page", 
      content: "This table displays the members of the organization",
      path:"/idm/home_orgs/"
    }
 ]);
/*
	rolesTour.addSteps([	
	]);	
*/

/*

*/



if(window.location.pathname === "/idm/" && !initTour.ended()){ 
	 startInitTour();
}
  
});
