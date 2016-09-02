var tourTemplate = "<div class='popover tour'>\
	<div class='arrow'></div>\
	<h3 class='popover-title'></h3>\
	<div class='popover-content'></div>\
	<div class='popover-navigation'><div class='btn-group'>\
	<button class='btn btn-default' data-role='prev' onclick='tourName.prev()'>« Prev</button>\
	<button class='btn btn-default' data-role='next' onclick='tourName.next()'>Next »</button>\
	</div>\
	<button class='btn btn-default' data-role='end' onclick='tourName.end()'>End tour</button>\
	</div>";

var appsTour = new Tour({
	name: "applicationsTour",
	debug: false,
	backdrop: true,
	template: function() {
		return tourTemplate.replace(/tourName/g, 'appsTour');
	},
	steps: [
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
		onShow: function (appsTour) {
			$("#id_name").val("FIWARE Wonder APP");
		}
	},
	{
		element: "#id_description",
		title: "Register an application", 
		content: "This is the description",
		path:"/idm/myApplications/create/",
		placement: "left",
		onShow: function (appsTour) {
			$("#id_description").val("Some description of the app.");
		}
	},
	{
		element: "#id_url",
		title: "Register an application", 
		content: "This is the url of your app",
		path:"/idm/myApplications/create/",
		placement: "left",
		onShow: function (appsTour) {
			$("#id_url").val("myappurl.com");
		}
	},
	{
		element: "#id_callbackurl",
		title: "Register an application", 
		content: "This is the callbackurl of your app.",
		path:"/idm/myApplications/create/",
		placement: "left",
		onShow: function (appsTour) {
			$("#id_callbackurl").val("myappurl.com/callback");
		},
		onNext: function (appsTour) {
			$(".btn-primary").click();
		}
	}
	]
});

var orgsTour = new Tour({
	name: "organizationsTour",
	debug: false,
	backdrop: true,
	template: function() {
		return tourTemplate.replace(/tourName/g, 'orgsTour');
	},
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
});

var rolesTour = new Tour({
	name: "rolesAndPermissionsTour",
	debug: false,
	backdrop: true,
	template: function() {
		return tourTemplate.replace(/tourName/g, 'rolesTour');
	},
});

var settingsTour = new Tour({
	name: "accountSettingsTour",
	debug: false,
	backdrop: true,
	template: function() {
		return tourTemplate.replace(/tourName/g, 'settingsTour');
	},
});