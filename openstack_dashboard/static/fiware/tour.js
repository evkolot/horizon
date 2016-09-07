var tourTemplate = "<div class='popover tour'>\
	<div class='arrow'></div>\
	<h3 class='popover-title'></h3>\
	<div class='popover-content'></div>\
	<div class='popover-navigation'><div class='btn-group'>\
	<button class='btn btn-default' data-role='prev'>« Prev</button>\
	<button class='btn btn-primary' data-role='next'>Next »</button>\
	</div>\
	<div class='btn-group'><button class='btn btn-default' data-role='end'>Exit</button></div>\
	</div>";

$.fn.extend({
	inputTextWithDelay: function(text, delay=40) {
		i = 0;
		$this = this;
		interval = setInterval(function() {
			$this.val($this.val() + text[i]);
			if (++i > text.length - 1)
				return clearInterval(interval);
		}, delay);
	}
});

var tours = {

	initTour: new Tour({
		name: "getStartedTour",
		debug: true,
		backdrop: true,
		backdropPadding: 5,
		template: tourTemplate,
		onRedirectError: function (tour) {
			tour.end();
			document.location.href = "/idm/";
		},
		steps: [
		{
			path: "/idm/",
			title: "Let's get started!",
			content: "Welcome to the FIWARE's KeyRock Identity Manager. This is a basic tour that will guide you through the basics.",
			orphan: true
		},
		{
			path: "/idm/",
			element: "header",
			title: "FIWARE Portal",
			content: "The FIWARE's IdM is part of FIWARE Lab. You can check some other FIWARE Lab components in the header bar.",
			placement: "bottom"
		},
		{
			path: "/idm/",
			element: "#profile_editor_switcher",
			title: "Your Profile",
			content: "Use this section to access your profile, the settings and to log out.",
			placement: "bottom"
		},
		{
			path: "/idm/",
			element: "nav.sidebar",
			title: "Navigation",
			content: "You can find the different sections of KeyRock in this sidebar.",
			placement: "right"
		},
		{
			path: "/idm/",
			element: "#applications",
			title: "Applications",
			content: "Applications are the experiments with the FIWARE technology you participate on (e.g. as an owner or purchaser). This table shows a quick summary of them.",
			placement: "right"
		},
		{
			path: "/idm/",
			element: "#organizations",
			title: "Organizations",
			content: "Organizations are basically groups of users. They come in very handy when you want to authorize several users in your application at once. A quick summary of them can be found in this table.",
			placement: "left"
		},
		{
			path: "/idm/",
			title: "You're all set!",
			content: "<p>You finished the basics Tour! You can now head on to the next Tour and learn more about aplications and how to register one or exit this tutorial and start experimenting yourself.</p>Thank you for using FIWARE Lab!",
			orphan: true,
			onShown: function (tour) {
				$(".popover.tour .btn-group:last-child").append('<button class="btn btn-primary next-tour" data-current-tour="initTour" data-next-tour="appsTour">Next Tour</button>');
			},
			onHide: function (tour) {
				$(".popover.tour .btn-group:last-child").remove();
			}
		},
		]
	}),

	appsTour: new Tour({
		name: "applicationsTour",
		debug: false,
		backdrop: true,
		template: tourTemplate,
		onRedirectError: function (tour) {
			tour.end();
			document.location.href = "/idm/";
		},
		steps: [
		{
			path: "/idm/",
			title: "Applications Tour",
			content: "Welcome to the Applications Tour! You will now learn how to register an application in KeyRock.",
			orphan: true
		},
		{
			path: "/idm/",
			element: "#applications .btn-group",
			title: "Registering a new application",
			content: "The quickest way to register a new application is this button. Click on it to register your first application!",
			placement: "right",
			reflex: true
		},
		{
			path: "/idm/myApplications/create/",
			element: "#create_application_modal",
			title: "Registering a new application: STEP 1",
			content: "This form contains the basic information required to create a new application.",
			placement: "left",
			orphan: true
		},
		{
			path: "/idm/myApplications/create/",
			element: "#id_name",
			title: "Registering a new application: STEP 1",
			content: "This is the name of your application.",
			placement: "left",
			onShown: function (tour) {
				$("#id_name").inputTextWithDelay("First App");
			}
		},
		{
			path: "/idm/myApplications/create/",
			element: "#id_description",
			title: "Registering a new application: STEP 1",
			content: "Provide here a longer description for your application.",
			placement: "left",
			onShown: function (tour) {
				$("#id_description").inputTextWithDelay("Created during the Applications Tour.");
			}
		},
		{
			path: "/idm/myApplications/create/",
			element: "#id_url",
			title: "Registering a new application: STEP 1",
			content: "This is the URL of your app. This field is required to check that requests to KeyRock regarding your app (e.g. when using OAuth to authorize users) come actually from your app.",
			placement: "left",
			onShown: function (tour) {
				$("#id_url").inputTextWithDelay("sample.app.com");
			}
		},
		{
			path: "/idm/myApplications/create/",
			element: "#id_callbackurl",
			title: "Register an application: STEP 1",
			content: "This is the callback URL of your application. KeyRock will redirect the User Agent back to it after an OAuth authorization flow.",
			placement: "left",
			onShown: function (tour) {
				$("#id_callbackurl").inputTextWithDelay("sample.app.com/login");
			}
		},
		{
			path: "/idm/myApplications/create/",
			element: ".btn.btn-primary",
			title: "Register an application: STEP 1",
			content: "Click this button to continue.",
			placement: "left",
			reflex: true,
			onNext: function (tour) {
				$(".btn-primary").click();
			}
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/avatar\/", "i"),
			element: "#upload_image_modal",
			title: "Register an application: STEP 2",
			content: "In this step you can choose an image for your app. We will leave the default one.",
			placement: "left",
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/avatar\/", "i"),
			element: ".btn.btn-primary",
			title: "Register an application: STEP 2",
			content: "Click this button to continue.",
			placement: "left",
			reflex: true,
			onNext: function (tour) {
				$(".btn-primary").click();
			}
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/roles\/", "i"),
			element: "#create_application_roles",
			title: "Register an application: STEP 3",
			content: "In this last step, you can manage the roles and permissions of your app. We won't change anything now, but you can learn more about them in the next Tour.",
			placement: "left"
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/roles\/", "i"),
			element:  ".btn.btn-primary",
			title: "Register an application: STEP 3",
			content: "Click this button when you're done editing your new app.",
			placement: "left",
			reflex: true,
			onNext: function (appsTour) {
				$(".btn-primary").click();
				return (new jQuery.Deferred()).promise();
			}
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/", "i"),
			element:  "#detailApplication",
			title: "Check out your new application",
			content: "This is the detail page of your new app. You can find the OAuth credentials and register a PEP Proxy or some IoT Sensors. This is the end of th",
			placement: "left"
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/", "i"),
			title: "You're all set!",
			content: "This is the end of the tour. If you want to learn more about roles and permissions in apps, click <a href='#' class='next-tour' data-current-tour='appsTour' data-next-tour='rolesTour'>here</a>. Otherwise click 'End tour' to exit and start experimenting yourself. Thank you for using FIWARE Lab!",
			orphan: true
		},
		]
	}),

	orgsTour: new Tour({
		name: "organizationsTour",
		debug: false,
		backdrop: true,
		template: tourTemplate,
		steps: [
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
			onNext: function (appsTour) {
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
		},
		]
	}),

	rolesTour: new Tour({
		name: "rolesAndPermissionsTour",
		debug: false,
		backdrop: true,
		template: tourTemplate,
	}),

	settingsTour: new Tour({
		name: "accountSettingsTour",
		debug: false,
		backdrop: true,
		template: tourTemplate,
	})
};

$( document ).ready(function() {
	$("body").on("click", ".next-tour", function() {
		var nextTour = $(this).attr('data-next-tour');
		var currentTour = $(this).attr('data-current-tour');

		tours[currentTour].end();
		tours[nextTour].init();
		tours[nextTour].start();
	});

	$.each(tours, function(i, val) {
		if (!val.ended()) {
			val.init();
			return false;
		}
	});

});
