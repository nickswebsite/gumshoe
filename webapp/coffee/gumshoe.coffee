class Url
  constructor: ( @url ) ->
    @scheme = null
    @host = null
    @path = null
    @params = {}
    @query = {}
    @fragment = null

    uri = new URI.parse( @url )
    @scheme = uri.protocol
    @host = uri.hostname
    @path = uri.path
    @fragment = uri.fragment
    if uri.query
      @query = URI.parseQuery( uri.query )

class User
  constructor: ( @id, @username, @firstName, @lastName, @email = "" ) ->

  @fromDTO: ( dto ) -> new User( dto.id, dto.username, dto.firstName, dto.lastName, dto.email )

class UserManager
  constructor: () ->
    @users = {}

  putUser: ( user ) -> @users[user.id] = user
  getUserById: ( userId ) -> @users[userId] || null
  getAll: () -> ( user for _, user of @users )
  getDefaultUser: () -> @users[0]

userManager = new UserManager()

class Version
  constructor: ( @id, @name, @description = "" ) ->

  @fromDTO: ( dto ) -> new Version( dto.id, dto.name, dto.description )

class Component
  constructor: ( @id, @name, @description = "" ) ->

  @fromDTO: ( dto ) -> new Component( dto.id, dto.name, dto.description )

class Project
  constructor: () ->
    @id = -1
    @name = ""
    @description = ""
    @issueKey = ""
    @components = []
    @versions = []
    @priorities = []
    @issueTypes = []
    @resolutions = []

  findComponentById: ( id ) -> ( @components.filter ( obj ) -> obj.id == id )[0] || null
  findVersionById: ( id ) -> ( @versions.filter ( obj ) -> obj.id == id )[0] || null
  findPriorityByShortName: ( shortName ) -> ( @priorities.filter ( obj ) -> obj.shortName == shortName )[0] || null
  getDefaultPriority: () ->
    filtered = @priorities.filter ( item ) -> item.shortName == "NP"
    if filtered.length != 0
      defaultPriority = filtered[0]
    else
      defaultPriority = @priorities[0]
    defaultPriority

  @fromDTO: (dto) ->
    obj = new Project()
    obj.id = dto.id
    obj.name = dto.name
    obj.description = dto.description
    obj.issueKey = dto.issueKey
    obj.components = ( Component.fromDTO( component ) for component in dto.components )
    obj.versions = ( Version.fromDTO( version ) for version in dto.versions )
    obj.issueTypes = ( IssueType.fromDTO( type ) for type in dto.issueTypes )
    obj.resolutions = ( Resolution.fromDTO( resolution ) for resolution in dto.resolutions )
    obj.priorities = ( Priority.fromDTO( priority ) for priority in dto.priorities )
    obj

class NullProject extends Project
  constructor: () -> super()
  findComponentById: ( id ) -> null
  findVersionById: ( id ) -> null
  findPriorityByShortName: ( id ) -> null

class ProjectManager
  constructor: () ->
    @projects = {}

  putProject: ( project ) -> @projects[project.id] = project
  getProject: ( id ) -> @projects[id] || null
  allProjects: () -> ( project for _, project of @projects )

projectManager = new ProjectManager()

class Priority
  constructor: ( @id, @name, @shortName, @wieght ) ->

  @fromDTO: ( dto ) -> new Priority( dto.id, dto.name, dto.shortName, dto.weight )

class IssueType
  constructor: ( @id=-1, @name="", @shortName="" ) ->

  @fromDTO: ( dto ) ->
    switch dto
      when "BUG" then IssueType.BUG
      when "FRQ" then IssueType.FEATURE_REQUEST
      when "TASK" then IssueType.TASK

  @BUG: new IssueType( 1, "Bug", "BUG", 30 )
  @FEATURE_REQUEST: new IssueType( 2, "Feature Request", "FRQ", 20 )
  @TASK: new IssueType( 3, "Task", "TASK", 10 )

class Resolution
  constructor: ( @id, @name ) ->

  @fromDTO: ( dto ) ->
    switch dto
      when "UNRESOLVED" then Resolution.UNRESOLVED
      when "INVALID" then Resolution.INVALID
      when "WONT_FIX" then Resolution.WONT_FIX
      when "FIXED" then Resolution.FIXED

  @UNRESOLVED: new Resolution( "UNRESOLVED", "Unresolved" )
  @INVALID: new Resolution( "INVALID", "Invalid" )
  @WONT_FIX: new Resolution( "WONT_FIX", "Won't Fix" )
  @FIXED: new Resolution( "FIXED", "Fixed" )

class Milestone
  constructor: ( @id, @name, @description = "" ) ->

  @fromDTO: ( dto ) -> new Milestone( dto.id, dto.name, dto.description || "" )

class MilestoneManager
  constructor: () ->
    @milestones = {}

  putMilestone: ( milestone ) ->
    @milestones[milestone.id] = milestone

  getMilestoneById: ( id ) -> @milestones[id] || null
  getAllMilestones: () -> ( milestone for _, milestone of @milestones )

milestoneManager = new MilestoneManager()

class Status
  constructor: ( @resolution, @id, @name ) ->

  @fromDTO: ( dto, resolution = null ) ->
    switch dto
      when "OPEN" then new OpenStatus()
      when "RESOLVED" then new ResolvedStatus( Resolution.fromDTO( resolution ) )
      when "CLOSED" then new ClosedStatus( { resolution: resolution } )

class OpenStatus extends Status
  constructor: () -> super( Resolution.UNRESOLVED, "OPEN", "Open" )

class ResolvedStatus extends Status
  constructor: ( resolution = Resolution.FIXED ) -> super( resolution, "RESOLVED", "Resolved" )

class ClosedStatus extends Status
  constructor: ( oldStatus ) -> super( oldStatus.resolution, "CLOSED", "Closed" )

class Comment
  constructor: ( url, author, text, created, updated) ->
    @url = url || null
    @created = created || new Date()
    @updated = updated || new Date()
    @author = author || null
    @text = text || ""

  @fromDTO: ( dto ) ->
    created = if dto.created then new Date( dto.created ) else new Date()
    updated = if dto.updated then new Date( dto.updated ) else new Date()

    author = userManager.getUserById( dto.author.id )
    if !author
      author = User.fromDTO( dto.author )
      userManager.putUser( User.fromDTO( dto.author ) )

    new Comment( dto.url, author, dto.text, created, updated )

class Issue
  constructor: () ->
    @issueKey = null

    @issueType = IssueType.BUG
    @project = null
    @priority = null

    @summary = ""
    @description = ""
    @stepsToReproduce = ""

    @assignee = null
    @reporter = userManager.getDefaultUser()

    @components = []
    @affectsVersions = []
    @fixVersions = []

    @milestone = null

    @status = new OpenStatus()

    @comments = []

    @reported = new Date()
    @lastUpdated = new Date()

    @commentsUrl = null

  @fromDTO: ( dto ) ->
    obj = new Issue()
    obj.issueKey = dto.issueKey
    obj.project = projectManager.getProject( dto.project )
    obj.issueType = IssueType.fromDTO( dto.issueType )
    obj.priority = obj.project.findPriorityByShortName( dto.priority )

    obj.summary = dto.summary
    obj.description = dto.description
    obj.stepsToReproduce = dto.stepsToReproduce

    obj.components = ( obj.project.findComponentById( componentId ) for componentId in dto.components )
    obj.affectsVersions = ( obj.project.findVersionById( versionId ) for versionId in dto.affectsVersions )
    obj.fixVersions = ( obj.project.findVersionById( versionId ) for versionId in dto.fixVersions )

    obj.status = Status.fromDTO( dto.status )
    obj.resolution = Resolution.fromDTO( dto.resolution )

    if dto.milestone
      obj.milestone = milestoneManager.getMilestoneById( dto.milestone.id )

    obj.assignee = userManager.getUserById( dto.assignee.id )
    obj.reporter = userManager.getUserById( dto.reporter.id )

    obj.reported = new Date( dto.reported )
    obj.lastUpdated = new Date( dto.lastUpdated )

    obj.commentsUrl = dto.commentsUrl

    obj

  resolve: ( resolution ) ->
    if @status.id == "OPEN"
      if resolution.id != "UNRESOLVED"
        @status = new ResolvedStatus( resolution )

  reopen: () ->
    if @status.id != "OPEN"
      @status = new OpenStatus()

  close: () ->
    if @status.id == "RESOLVED"
      @status = new ClosedStatus( @status )

class IssueFilter
  constructor: ( @allProjects = null, @allStatuses = null, @allUsers = null, @allMilestones = null ) ->
    @allProjects = @allProjects || []
    @allStatuses = @allStatuses || []
    @allVersions = @allVersions || []
    @allUsers = @allUsers || []
    @allMilestones = @allMilestones || []

    @projectsSelected = []
    @statusesSelected = []
    @affectsVersionsSelected = []
    @fixVersionsSelected = []
    @assigneesSelected = []
    @milestonesSelected = []

    @noAffectsVersion = { id: -1, name: "No Affects Version" }
    @noFixVersion = { id: -1, name: "No Fix Version" }

  getAvailableVersions: ( initial ) ->
    projects = @projectsSelected
    if projects.length == 0
      projects = @allProjects
    versions = if initial then [ initial ] else []
    for project in projects
      for version in project.versions
        versions.push version
    versions

  getAvailableFixVersions: () -> @getAvailableVersions()

  getAvailableAffectsVersions: () -> @getAvailableVersions()

  setSelectedAssigneesByIds: ( ids ) ->
    @assigneesSelected = @allUsers.filter ( item ) -> ids.indexOf( item.id ) != -1

  setSelectedStatuses: ( ids ) ->
    @statusesSelected = ids

  setSelectedProjectsByIds: ( ids ) ->
    @projectsSelected = @allProjects.filter ( item ) -> ids.indexOf( item.id ) != -1

  setSelectedMilestones: ( ids ) ->
    @milestonesSelected = @allMilestones.filter ( item ) -> ids.indexOf( item.id ) != -1

  setSelectedFixVersionsByIds: ( ids ) ->
    @fixVersionsSelected = @getAvailableFixVersions().filter ( item ) -> ids.indexOf( item.id ) != -1

  setSelectedAffectsVersionsByIds: ( ids ) ->
    @affectsVersionsSelected = @getAvailableAffectsVersions().filter ( item ) -> ids.indexOf( item.id ) != -1

  getServerParams: () ->
    ret = {}
    if @projectsSelected.length != 0
      ret.projects = ( p.issueKey for p in @projectsSelected ).join( "," )
    if @statusesSelected.length != 0
      ret.statuses = ( s.toUpperCase() for s in @statusesSelected ).join( "," )
    if @affectsVersionsSelected.length != 0
      ret.affects_versions = ( v.id.toString() for v in @affectsVersionsSelected ).join( "," )
    if @fixVersionsSelected.length != 0
      ret.fix_versions = ( v.id.toString() for v in @fixVersionsSelected ).join( "," )
    if @assigneesSelected.length != 0
      ret.assignees = ( a.id.toString() for a in @assigneesSelected ).join( "," )
    if @milestonesSelected.length != 0
      ret.milestones = ( m.id.toString() for m in @milestonesSelected ).join( "," )
    ret

class HeaderOrderingFilter
  constructor: ( @name, direction = HeaderOrderingFilter.DESCENDING_ASCENDING ) ->
    @upText = "\u25B2"
    @downText = "\u25BC"
    @noneText = ""

    @ascDscNon = direction

    @direction = HeaderOrderingFilter.NONE
    @directionText = @noneText

  setNone: () ->
    @direction = HeaderOrderingFilter.NONE
    @directionText = @noneText

  setAscending: () ->
    @direction = HeaderOrderingFilter.ASCENDING
    @directionText = @upText

  setDescending: () ->
    @direction = HeaderOrderingFilter.DESCENDING
    @directionText = @downText

  setState: ( state ) ->
    switch ( state )
      when HeaderOrderingFilter.DESCENDING
        @setDescending()
      when HeaderOrderingFilter.ASCENDING
        @setAscending()
      when HeaderOrderingFilter.NONE
        @setNone
      else
        @setNone

  toggle: () ->
    if @ascDscNon
      switch @direction
        when HeaderOrderingFilter.ASCENDING
          @setDescending()
        when HeaderOrderingFilter.DESCENDING
          @setNone()
        when HeaderOrderingFilter.NONE
          @setAscending()

    else
      switch @direction
        when HeaderOrderingFilter.ASCENDING
          @setNone()
        when HeaderOrderingFilter.DESCENDING
          @setAscending()
        when HeaderOrderingFilter.NONE
          @setDescending()

  @ASCENDING: "ASC"
  @DESCENDING: "DSC"
  @NONE: "NONE"

  @ASCENDING_DESCENDING = true
  @DESCENDING_ASCENDING = false

@Gumshoe =
  User: User
  UserManager: UserManager
  userManager: userManager
  Version: Version
  Component: Component
  Project: Project
  NullProject: NullProject
  ProjectManager: ProjectManager
  projectManager: projectManager
  IssueType: IssueType
  Issue: Issue
  Comment: Comment
  Priority: Priority
  Status: Status
  OpenStatus: OpenStatus
  ResolvedStatus: ResolvedStatus
  ClosedStatus: ClosedStatus
  Resolution: Resolution
  Milestone: Milestone
  MilestoneManager: MilestoneManager
  milestoneManager: milestoneManager
  IssueFilter: IssueFilter
  HeaderOrderingFilter: HeaderOrderingFilter

@Url = Url
