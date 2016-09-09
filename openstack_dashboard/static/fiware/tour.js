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

var noButtonsTemplate = "<div class='popover tour'>\
	<div class='arrow'></div>\
	<h3 class='popover-title'></h3>\
	<div class='popover-content'></div>\
	<div class='popover-navigation'><div class='btn-group'>\
	</div>\
	<div class='btn-group'><button class='btn btn-default' data-role='end'>Exit</button></div>\
	</div>";

$.fn.extend({
	inputTextWithDelay: function(text, delay=40) {
		if (this.val() !== '')
			return void 0;

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
		keyboard: false,
		onRedirectError: function (tour) {
			tour.end();
			document.location.href = "/idm/";
			window.console.log("Bootstrap Tour '" + tour._options.name + "' | " + 'Redirection error');
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
		backdropPadding: 5,
		template: tourTemplate,
		keyboard: false,
		onRedirectError: function (tour) {
			tour.end();
			document.location.href = "/idm/";
			window.console.log("Bootstrap Tour '" + tour._options.name + "' | " + 'Redirection error');
		},
		steps: [
		{
			path: "/idm/",
			title: "Applications Tour",
			content: "Welcome to the Applications Tour! You will now learn how to register an application in KeyRock.",
			orphan: true,
		},
		{
			path: "/idm/",
			element: "#applications",
			title: "Registering a new application", 
			content: "The quickest way to register a new application is the 'Register' button here. Click on it to register your first application!",
			placement: "right",
			reflex: true,
			reflexElement: "#applications .btn-group"
		},
		{
			path: "/idm/myApplications/create/",
			element: "#create_application_modal",
			title: "<p>STEP 1:</p>Registering a new application",
			content: "<p>This form contains the basic information required to create a new application.</p>First of all, provide a name and a longer description for your it.",
			placement: "left",
			onShown: function (tour) {
				$("#id_name").inputTextWithDelay("First App");
				setTimeout(function() {
					$("#id_description").inputTextWithDelay("Created during the Applications Tour.");
				}, 750);
			}
		},
		{
			path: "/idm/myApplications/create/",
			element: "#create_application_modal fieldset .form-group:eq(2)",
			title: "<p>STEP 1:</p>Registering a new application",
			content: "This is the URL of your app. This field is required to check that requests to KeyRock regarding your app (e.g. when using OAuth to authorize users) come actually from your app.",
			placement: "left",
			onShown: function (tour) {
				$("#id_url").inputTextWithDelay("sample.app.com");
			}
		},
		{
			path: "/idm/myApplications/create/",
			element: "#create_application_modal fieldset .form-group:eq(3)",
			title: "<p>STEP 1:</p>Registering a new application",
			content: "This is the callback URL of your application. KeyRock will redirect the User Agent back to it after an OAuth authorization flow.",
			placement: "left",
			onShown: function (tour) {
				$("#id_callbackurl").inputTextWithDelay("sample.app.com/login");
			}
		},
		{
			path: "/idm/myApplications/create/",
			element: ".btn.btn-primary",
			title: "<p>STEP 1:</p>Registering a new application",
			content: "Click on this button to continue to the next step.",
			placement: "left",
			reflex: true,
			template: noButtonsTemplate
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/avatar\/", "i"),
			element: "#upload_image_modal",
			title: "<p>STEP 2:</p>Registering a new application",
			content: "In this step you can choose an image for your app. We will leave the default one.",
			placement: "left",
			onShown: function (tour) {
				$('[data-role="prev"]').addClass('disabled').prop('disabled', true).prop('tabindex', -1);
			}
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/avatar\/", "i"),
			element: ".btn.btn-primary",
			title: "<p>STEP 2:</p>Registering a new application",
			content: "Click on this button to continue to the next step.",
			placement: "left",
			reflex: true,
			template: noButtonsTemplate
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/roles\/", "i"),
			element: "#create_application_roles",
			title: "<p>STEP 3:</p>Registering a new application",
			content: "In this last step, you can manage the roles and permissions of your app. We won't change anything now, but you can learn more about them in the next Tour.",
			placement: "left",
			onShown: function (tour) {
				$('[data-role="prev"]').addClass('disabled').prop('disabled', true).prop('tabindex', -1);
			}
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/step\/roles\/", "i"),
			element:  ".btn.btn-primary",
			title: "<p>STEP 3:</p>Registering a new application",
			content: "Click on this button when you're done editing your new app.",
			placement: "left",
			reflex: true,
			template: noButtonsTemplate
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/", "i"),
			element:  "#content_body",
			title: "Check out your new application",
			content: "This is the detail page of your new app. You can find here the OAuth credentials and register a PEP Proxy or some IoT Sensors.",
			placement: "left",
			onShown: function (tour) {
				$('[data-role="prev"]').addClass('disabled').prop('disabled', true).prop('tabindex', -1);
			}
		},
		{
			path: RegExp("\/idm\/myApplications\/[^\/]+\/", "i"),
			title: "You're all set!",
			content: "<p>You finished the Applications Tour! You can now head on to the next Tour and learn more about roles and permissions inside apps and how to manage them or exit this tutorial and start experimenting yourself.</p>Thank you for using FIWARE Lab!",
			orphan: true,
			onShown: function (tour) {
				$(".popover.tour .btn-group:last-child").append('<button class="btn btn-primary next-tour" data-current-tour="appsTour" data-next-tour="rolesTour">Next Tour</button>');
			},
			onHide: function (tour) {
				$(".popover.tour .btn-group:last-child").remove();
			}
		}
		]
	}),

	rolesTour: new Tour({
		name: "rolesAndPermissionsTour",
		debug: false,
		backdrop: true,
		template: tourTemplate,
	}),

	orgsTour: new Tour({
		name: "organizationsTour",
		debug: false,
		backdrop: true,
		backdropPadding: 5,
		template: tourTemplate,
		keyboard: false,
		onRedirectError: function (tour) {
			tour.end();
			document.location.href = "/idm/";
			window.console.log("Bootstrap Tour '" + tour._options.name + "' | " + 'Redirection error');
		},
		steps: [
		{
			path: "/idm/",
			title: "Organizations Tour",
			content: "Welcome to the Organizations Tour! You will now learn how to create an organization in KeyRock.",
			orphan: true
		},
		{
			path: "/idm/",
			element: "#organizations",
			title: "Creating a new organization", 
			content: "The quickest way to create a new organization is the 'Create' button here. Click on it to create your first organization!",
			placement: "left",
			reflex: true,
			reflexElement: "#organizations .btn-group"
		},
		{
			path: "/idm/organizations/create/",
			element: "#create_application_modal",
			title: "<p>Creating a new organization",
			content: "<p>This form contains the basic information required to create a new organization.</p>Just provide a name and a longer description for it.",
			placement: "left",
			onShown: function (tour) {
				$("#id_name").inputTextWithDelay("First Org");
				setTimeout(function() {
					$("#id_description").inputTextWithDelay("Created during the Organizations Tour.");
				}, 750);
			}
		},
		{
			path: "/idm/organizations/create/",
			element: ".btn.btn-primary",
			title: "Creating a new organization",
			content: "Click on this button when you're done to create your new organization.",
			placement: "left",
			reflex: true,
			template: noButtonsTemplate
		},
		{
			path: "/idm/home_orgs/",
			title: "Organization created!",
			content: "Your new organization was successfully created. This is its home page.",
			orphan: true
		},
		{
			path: "/idm/home_orgs/",
			element: "nav.sidebar",
			title: "Navigation",
			content: "There's a new section called 'Members' in the sidebar menu.",
			placement: "right"
		},
		{
			path: "/idm/home_orgs/",
			element: "#applications",
			title: "Applications",
			content: "These are the applications your organization participates on.",
			placement: "right"
		},
		{
			path: "/idm/home_orgs/",
			element: "#members",
			title: "Members",
			content: "This table shows a quick summary of the members of your organization.",
			placement: "left"
		},
		{
			path: "/idm/home_orgs/",
			element: "#profile_editor_switcher",
			title: "Organization profile",
			content: "Note that you are now logged in as your new organization. You can use this section to log back in with your personal account.",
			placement: "bottom"
		},
		{
			path: "/idm/",
			title: "You're all set!",
			content: "<p>You finished the Organizations Tour! You can now head on to the next Tour and learn more about the most important settings of your account or exit this tutorial and start experimenting yourself.</p>Thank you for using FIWARE Lab!",
			orphan: true,
			template: noButtonsTemplate,
			redirect: function () {
				document.location.href = $("#profile_editor_switcher .dropdown-menu .dropdown-menu li:last a").attr('href');
			},
			onShown: function (tour) {
				$(".popover.tour .btn-group:last-child").append('<button class="btn btn-primary next-tour" data-current-tour="orgsTour" data-next-tour="settingsTour">Next Tour</button>');
			},
			onHide: function (tour) {
				$(".popover.tour .btn-group:last-child").remove();
			}
		},
		]
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

	$.each(tours, function(i, tour) {
		if (tour._getState('current_step')!== null && !tour.ended()) {
			tour.init();
			return false;
		}
	});

});
