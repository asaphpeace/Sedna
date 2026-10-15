// Where the Hub's Knowledge Base and Help Center entries point. Articles stay
// in Zendesk (support.sedna.com); VMS documentation lives on docs.dataloy.com.
const HC = 'https://support.sedna.com/hc/en-us'

export const SUPPORT = {
  home: HC,
  search: (q: string) => `${HC}/search?query=${encodeURIComponent(q)}`,
  emailDocs: `${HC}/categories/31081504755991-Learn`,
  vmsDocs: 'https://docs.dataloy.com/voyage-management-system',
  fix: `${HC}/categories/31163351231255-Fix`,
  optimise: `${HC}/categories/31163403803159-Optimise`,
  requests: `${HC}/requests`,
  newRequest: `${HC}/requests/new`,
  whatIsEmail: `${HC}/articles/32631905877271-What-is-Stream`,
  getToKnowSedna: `${HC}/articles/32687596207511-Get-to-Know-Sedna-in-5-Minutes`,
  levelOne: `${HC}/sections/31990104900247--Level-One-Start-Smart`,
  levelTwo: `${HC}/sections/31990059177623--Level-Two-Power-Up-Your-Inbox`,
  levelThree: `${HC}/sections/32633624549399--Level-Three-Collaborate-Command`,
  // VMS support cases are raised in the Jira service desk portal
  vmsPortal: 'https://dataloy-cloud.atlassian.net/servicedesk/customer/portal/5',
}
