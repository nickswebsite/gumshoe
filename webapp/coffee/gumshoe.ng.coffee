# Imports
IssueFilter = Gumshoe.IssueFilter
HeaderOrderingFilter = Gumshoe.HeaderOrderingFilter
NullProject = Gumshoe.NullProject
Comment = Gumshoe.Comment
Issue = Gumshoe.Issue
Project = Gumshoe.Project
projectManager = Gumshoe.projectManager
ProjectManager = Gumshoe.ProjectManager
Milestone = Gumshoe.Milestone
User = Gumshoe.User
UserManager = Gumshoe.UserManager
userManager = Gumshoe.userManager
MilestoneManager = Gumshoe.MilestoneManager
milestoneManager = Gumshoe.milestoneManager

# GLOBAL APP LEVEL CONSTANTS
PAGES =
  ISSUES_ADD: "/forms/add_issue"
  ISSUES_LIST: "/"
  USER_HOME: "/"

API =
  ISSUES_LIST: "/rest/issues/"

class IssueListCtrl
  @$inject = [ "$scope", "$http", "$q", "searchService", "projectsService", "usersService", "milestonesService" ]

  constructor: ( @scope, @http, @q, @searchService, @projectsService, @usersService, @milestonesService ) ->
    @scope.issues = []
    @scope.issuesFilter = new IssueFilter( @projectsService.getAll(),
                                          [ "Open", "Resolved", "Closed" ],
                                          @usersService.getAll(),
                                          @milestonesService.getAll() )
    @scope.totalIssues = 0
    @scope.currentPage = 1
    @scope.pageSize = 25
    @scope.totalPages = 1

    @scope.pageSizeOptions = [ 5, 10, 25, 50 ]

    @scope.priorityHeader = new HeaderOrderingFilter( "Priority" )
    @scope.priorityHeader.setDescending()
    @scope.issueKeyHeader = new HeaderOrderingFilter( "Summary" )
    @scope.resolutionHeader = new HeaderOrderingFilter( "Resolution" )
    @scope.assigneeHeader = new HeaderOrderingFilter( "Assignee" )

    @scope.refresh = () => @fetchIssueList()
    @scope.addIssue = () => @addIssue()
    @scope.saveSettings = () => @saveSearchSettings()

    @scope.$on "navbar.search.submit", ( evt, data ) =>
      @fetchIssueList()

    @http.get( "/rest/settings/" ).success( ( data, status, headers, config ) =>
      if !data.unsaved
        @restoreSearchSettings( data )
      else
        @fetchIssueList()
    )

    @scope.$watch "currentPage", ( newValue, oldValue ) =>
      if newValue && newValue != oldValue
        @fetchIssueList()

    @scope.$watch "pageSize", ( newValue, oldValue ) =>
      if newValue && newValue != oldValue
        @fetchIssueList()

    @scope.$watch "priorityHeader.direction", ( newValue, oldValue ) =>
      if newValue && newValue != oldValue
        @fetchIssueList()

    @scope.watch "issueKeyHeader.direction", ( newValue, oldValue ) =>
      if newValue && newValue != oldValue
        @fetchIssueList()

    @scope.watch "resolutionHeader.direction", ( newValue, oldValue ) =>
      if newValue && newValue != oldValue
        @fetchIssueList()

  toServerParam: ( headerFilter, paramName ) ->
    if headerFilter.direction == HeaderOrderingFilter.DESCENDING then paramName else "-#{paramName}"

  addIssue: () ->
    if @scope.issuesFilter.projectsSelected.length != 1
      alert "Please select ONE project."
    else
      projectId = @scope.issuesFilter.projectsSelected[0].id
      @saveSearchSettings().then( () =>
        window.location = "/forms/add_issue?project=#{projectId}"
      )

  saveSearchSettings: () ->
    defered = @q.defer()

    dto =
      projects: ( project.id for project in @scope.issuesFilter.projectsSelected )
      statuses: ( status for status in @scope.issuesFilter.statusesSelected )
      milestones: ( milestone.id for milestone in @scope.issuesFilter.milestonesSelected )
      fixVersions: ( fixVersion.id for fixVersion in @scope.issuesFilter.fixVersionsSelected )
      affectsVersions: ( version.id for version in @scope.issuesFilter.affectsVersionsSelected )
      assignees: ( user.id for user in @scope.issuesFilter.assigneesSelected )
      currentPage: @scope.currentPage
      pageSize: @scope.pageSize
      searchTerms: @searchService.getSearchTerms()
      ordering:
        priority: @scope.priorityHeader.direction
        issueKey: @scope.issueKeyHeader.direction
        resolution: @scope.resolutionHeader.direction

    @http.put( "/rest/settings/", dto).success( () =>
      defered.resolve()
    ).error ( () =>
      defered.reject()
    )

    defered.promise

  restoreSearchSettings: ( dto ) ->
    @scope.issuesFilter.setSelectedProjectsByIds( dto.projects || [] )
    @scope.issuesFilter.setSelectedStatuses( dto.statuses || [] )
    @scope.issuesFilter.setSelectedFixVersionsByIds( dto.fixVersions || [] )
    @scope.issuesFilter.setSelectedAffectsVersionsByIds( dto.affectsVersions || [] )
    @scope.issuesFilter.setSelectedAssigneesByIds( dto.assignees || [] )
    @scope.issuesFilter.setSelectedMilestones( dto.milestones || [] )

    @searchService.setSearchTerms( dto.searchTerms || "" )

    @scope.pageSize = dto.pageSize
    @scope.currentPage = dto.currentPage

    if dto.ordering
      @scope.priorityHeader.setState( dto.ordering.priority )
      @scope.issueKeyHeader.setState( dto.ordering.issueKey )
      @scope.resolutionHeader.setState( dto.ordering.resolution )

    @fetchIssueList()

  fetchIssueList: () ->
    params = @scope.issuesFilter.getServerParams()
    params.page = @scope.currentPage
    params.page_size = @scope.pageSize

    orderByParams = []
    if @scope.priorityHeader.direction != HeaderOrderingFilter.NONE
      orderByParams.push @toServerParam( @scope.priorityHeader, "priority" )
    if @scope.issueKeyHeader.direction != HeaderOrderingFilter.NONE
      orderByParams.push @toServerParam( @scope.issueKeyHeader, "issue_key" )
    if @scope.resolutionHeader.direction != HeaderOrderingFilter.NONE
      orderByParams.push @toServerParam( @scope.resolutionHeader, "resolution" )

    if orderByParams.length != 0
      params.order_by = orderByParams.join( "," )

    terms = @searchService.getSearchTerms()
    if terms
      params.terms = terms

    @http.get( API.ISSUES_LIST, { params: params } ).success( ( data, status, headers, config ) =>
      @scope.issues = ( Issue.fromDTO( i ) for i in data.results )
      @scope.totalIssues = data.count
      @scope.totalPages = Math.ceil( @scope.totalIssues / @scope.pageSize )
      @nextPageLink = data.next
      @previousPageLink = data.previous
    )

class UpdateIssueCtrl
  @$inject = [ '$scope', '$http', '$location', 'projectsService', 'usersService', 'milestonesService' ]

  constructor: ( @scope, @http, @location, @projectsService, @usersService, @milestonesService ) ->
    url = new Url( @location.absUrl() )
    if url.path == '/forms/add_issue'
      @scope.addMode = true
    else
      @scope.addMode = false

    issueKey = null

    @scope.users = @usersService.getAll()
    @scope.milestones = @milestonesService.getAll()

    @scope.comments = null
    @scope.commentText = ""

    @issueEndpoint = "#{API.ISSUES_LIST}"
    @issueCommentsEndpoint = null

    if !@scope.addMode
      parts = url.path.split("/")
      issueKey = parts.pop()
      @issueEndpoint = "#{API.ISSUES_LIST}#{issueKey}/"
      @issueCommentsEndpoint = "#{@issueEndpoint}comments/"

      @http.get( @issueEndpoint ).success ( ( data, status, headers, config ) =>
        @scope.issue = Issue.fromDTO( data )
        @scope.project = @scope.issue.project
        @scope.resolution = @scope.issue.status.resolution

        @scope.issueTypes = @scope.project.issueTypes
        @scope.priorities = @scope.project.priorities
        @scope.resolutions = @scope.project.resolutions

        if @scope.comments
          @scope.issue.comments = @scope.comments
      )

      @http.get( @issueCommentsEndpoint ).success( ( data, status, headers, config ) =>
        @scope.comments = ( Comment.fromDTO( c ) for c in data )
        if @scope.issue
          @scope.issue.comments = @scope.comments
      )

    else
      @scope.project = @projectsService.getProject( parseInt( url.query.project ) )
      if !@scope.project
        @scope.project = new NullProject()
      @scope.issue = new Issue()
      @scope.issue.project = @scope.project
      @scope.issue.priority = @scope.project.getDefaultPriority()
      @scope.resolution = @scope.issue.status.resolution

      @scope.issueTypes = @scope.project.issueTypes
      @scope.priorities = @scope.project.priorities
      @scope.resolutions = @scope.project.resolutions

    @scope.save = () => @save( PAGES.USER_HOME )
    @scope.saveAndAdd = () => @saveAndAdd()
    @scope.cancel = () => @cancel()
    @scope.resolve = () => @resolve()
    @scope.reopen = () => @reopen()
    @scope.close = () => @close()
    @scope.addComment = () => @addComment( @scope.commentText )

    @scope.$on "navbar.search.submit", ( event, data ) =>
      dto =
        searchTerms: data.searchTerms

      @http.put( '/rest/settings/', dto ).success ( ( data, status, headers, config ) =>
        window.location = PAGES.ISSUES_LIST
      )

  addComment: ( text ) ->
    pl =
      text: text
    @http.post( @issueCommentsEndpoint, pl ).success ( ( data, status, headers, config ) =>
      @scope.comments.push Comment.fromDTO( data )
    )

  constructIssuePayload: ( issue ) ->
    id: issue.id
    project: issue.project.id
    summary: issue.summary
    issueType: issue.issueType.shortName
    priority: issue.priority.shortName
    description: issue.description
    stepsToReproduce: issue.stepsToReproduce

    status: issue.status.id
    resolution: issue.status.resolution.id

    assigneeId: if issue.assignee then issue.assignee.id else null
    milestoneId: if issue.milestone then issue.milestone.id else null

    components: ( component.id for component in issue.components )
    fixVersions: ( version.id for version in issue.fixVersions )
    affectsVersions: ( version.id for version in issue.affectsVersions )

  save: ( redirectUrl ) ->
    issuePayload = @constructIssuePayload( @scope.issue )
    if @scope.addMode
      uri = API.ISSUES_LIST
      method = "post"
    else
      uri = "#{API.ISSUES_LIST}#{@scope.issue.issueKey}/"
      method = "put"

    @http[method]( uri, issuePayload ).success ( (data, status, headers, config) =>
      if redirectUrl
        window.location = redirectUrl
    )

  saveAndAdd: () ->
    @save("#{PAGES.ISSUES_ADD}?project=#{@scope.issue.project.id}")

  cancel: () ->
    window.location = PAGES.USER_HOME

  resolve: () ->
    @scope.issue.resolve( @scope.resolution )
    @save()

  close: () ->
    @scope.issue.close()
    @save()

  reopen: () ->
    @scope.issue.reopen()
    @scope.resolution = @scope.issue.status.resolution
    @save()

class NavBarCtrl
  @$inject = [ '$scope', '$rootScope', 'searchService' ]

  constructor: ( @scope, @rootScope, @searchService ) ->
    @scope.searchTerms = ""
    @scope.submitSearch = () => @searchSubmitted()

    @scope.$watch 'searchTerms', () =>
      @searchService.setSearchTerms( @scope.searchTerms )

    @scope.$on 'search.terms.update', ( evt, data ) =>
      @scope.searchTerms = @searchService.getSearchTerms()

  searchSubmitted: () ->
    @rootScope.$broadcast("navbar.search.submit", { "searchTerms": @scope.searchTerms } )

gumshoe = angular.module( "gumshoe", [ 'gumshoe.initial', 'ui.bootstrap.pagination' ] )

# Register UpdateIssueCtrl
gumshoe.controller 'UpdateIssueCtrl', UpdateIssueCtrl
gumshoe.controller 'IssueListCtrl', IssueListCtrl
gumshoe.controller 'NavBarCtrl', NavBarCtrl

# Register projectService
gumshoe.factory 'projectsService', ['$http', 'PROJECTS', ( http, PROJECTS ) ->
  projectManager = projectManager || new ProjectManager()
  init: () ->
    for project in PROJECTS
      projectManager.putProject( Project.fromDTO( project ) )
  getProject: ( id ) -> projectManager.getProject( id )
  getAll: () -> projectManager.allProjects()
]

gumshoe.factory 'usersService', ['$http', 'USERS', ( http, USERS ) ->
  userManager = userManager || new UserManager()
  init: () ->
    for user in USERS
      userManager.putUser( User.fromDTO( user ) )
  getUserById: ( id ) -> userManager.getUserById( id )
  getAll: () -> userManager.getAll()
]

gumshoe.factory 'milestonesService', ['$http', 'MILESTONES', ( http, MILESTONES ) ->
  milestoneManager = milestoneManager || new MilestoneManager()
  init: () ->
    for milestone in MILESTONES
      milestoneManager.putMilestone( Milestone.fromDTO( milestone ) )
  getMilestonById: ( id ) -> milestoneManager.getMilestonById( id )
  getAll: () -> milestoneManager.getAllMilestones()
]

gumshoe.factory 'searchService', [ '$http', '$rootScope', ( http, rootScope ) ->
  currentSearchTerms = ""
  setSearchTerms: ( terms ) ->
    currentSearchTerms = terms
    rootScope.$broadcast "search.terms.update", {}
  getSearchTerms: () -> currentSearchTerms
]

# filter for debugger output
gumshoe.filter 'jsonPrint', () ->
  ( src ) -> JSON.stringify( src, undefined, 2)

# Initialize services
gumshoe.run [ 'projectsService', ( projectsService ) -> projectsService.init() ]
gumshoe.run [ 'usersService', ( usersService ) -> usersService.init() ]
gumshoe.run [ 'milestonesService', ( milestoneService ) -> milestoneService.init() ]

# configure CSRF compatiblity for django
gumshoe.config ["$httpProvider", ( $httpProvider ) ->
  $httpProvider.defaults.xsrfCookieName = "csrftoken"
  $httpProvider.defaults.xsrfHeaderName = "X-CSRFToken"
]

class Semiphore
  constructor: ( @stageCount, @callback ) -> @stagesDone = []

  signal: ( stage ) ->
    @stagesDone.push stage
    if @stagesDone.length >= @stageCount
      @callback()

# Start up AngularJS
bootstrap = () ->
  bootstrapAngular = () ->
    angular.element( document ).ready( () ->
      angular.bootstrap document, [ 'gumshoe' ]
    )

  semiphore = new Semiphore( 3, () => bootstrapAngular() )

  initInjector = angular.injector [ 'ng' ]
  initial = angular.module( 'gumshoe.initial', [] )
  http = initInjector.get '$http'
  http.get( "/rest/projects/" ).success( ( data ) ->
    initial.constant "PROJECTS", data
    semiphore.signal 'PROJECTS'
  )

  http.get( "/rest/users/" ).success( ( data ) ->
    initial.constant "USERS", data
    semiphore.signal 'USERS'
  )

  http.get( "/rest/milestones" ).success( ( data ) ->
    initial.constant "MILESTONES", data
    semiphore.signal "MILESTONES"
  )

bootstrap()
