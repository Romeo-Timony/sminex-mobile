# Backend endpoint inventory from `app-dev.apk`

Generated from Retrofit annotations in a JADX 1.5.5 decompilation of version 3.2.0. It is a static client inventory: it shows the calls the APK can make, but not which calls every user state will execute.

## Base URLs found in the APK

- `https://apigateway-sc-dev.sminex.digital/` — development build base URL.
- `apigateway-sc-preprod.sminex.digital` and `apigateway-sc.sminex.digital` are also embedded host names.

## Authentication flow required by `test_otp_login.py`

| Step | Request | Required response |
| --- | --- | --- |
| Request phone OTP | `POST /api/v1/auth/send`, `application/x-www-form-urlencoded`, field `phone_number` | `200 {"code":"1111"}` (`OtpResponse`) |
| Exchange OTP for tokens | `POST /api/v1/auth/token`, form fields `client_id`, `grant_type`, `code`, `phone_number` | `LoginResponse`: `access_token`, `refresh_token`, `expires_in`, `not-before-policy`, `refresh_expires_in`, `scope`, `session_state`, `token_type` |
| Refresh tokens | `POST /api/v1/auth/token`, form fields `client_id`, `grant_type`, `refresh_token` | same `LoginResponse` |

The OTP mock must cover both first and second calls. The token response must contain syntactically valid tokens and the downstream endpoints loaded after login; returning only `{"code":"1111"}` opens the OTP screen but cannot complete login.

## Retrofit endpoint inventory

| Service | Method | HTTP | Path | Request fields | Response DTO |
| --- | --- | --- | --- | --- | --- |
| ActivitiesRemoteApi | getEventsList | GET | /api/v1/activities/comfort/events | projectId, page, pageSize | m75 |
| ActivitiesRemoteApi | getEventById | GET | /api/v1/activities/comfort/events/{id} | id | Response body not typed |
| PrivilegesApi | putEventsRegister | PUT | /api/v1/activities/events/{eventId}/register | eventId | Response body not typed |
| CamerasService | getCameras | GET | /api/v1/cameras | projectId | Response body not typed |
| CountersRemoteAPI | getCounterHistory | GET | /api/v1/counters/{id}/history | id | Response body not typed |
| CountersRemoteAPI | sendReadings | POST | /api/v1/counters/{id}/readings | id, body | Response body not typed |
| CountersRemoteAPI | getAvailableCountersNumberByPremises | GET | /api/v1/counters/availableCounts | projectId | Response body not typed |
| CountersRemoteAPI | getCountersResourcesList | GET | /api/v1/counters/resources | none | Response body not typed |
| InvoicesRemoteAPI | getBalances | GET | /api/v1/finances/balances | projectId, personalAccountId | Response body not typed |
| InvoicesRemoteAPI | getPaymentDetails | GET | /api/v1/finances/balances/{balanceTypeAlias}/paymentDetail | balanceTypeAlias, projectId, invoiceId, personalAccountId | Response body not typed |
| InvoicesRemoteAPI | getBalanceByType | GET | /api/v1/finances/balances/{type} | type, projectId, personalAccountId | Response body not typed |
| InvoicesRemoteAPI | getBalancesHistory | GET | /api/v1/finances/balances/invoices | projectId, personalAccountId, balanceTypeAlias, periodFrom, periodTo, page, pageSize | fm0 |
| InvoicesRemoteAPI | removeCard | DELETE | /api/v1/finances/cards/{id} | id | lbg |
| InvoicesRemoteAPI | getInvoice | GET | /api/v1/finances/invoices/{invoiceId} | invoiceId | Response body not typed |
| InvoiceFileRemoteAPI | getInvoiceFile | GET | /api/v1/finances/invoices/{invoiceId}/file | invoiceId | Response body not typed |
| BalancesRemoteAPI | getBalanceList | GET | /api/v1/finances/invoices/balance | projectId | Response body not typed |
| FiltersRemoteAPI | getCustomers | GET | /api/v1/finances/invoices/customers | projectId | Response body not typed |
| FiltersRemoteAPI | getPremises | GET | /api/v1/finances/invoices/premises | projectId | Response body not typed |
| TypesRemoteAPI | getTypeList | GET | /api/v1/finances/invoices/types | projectId | Response body not typed |
| InvoicesRemoteAPI | getPersonalAccounts | GET | /api/v1/finances/personalAccounts | projectId | Response body not typed |
| IntercomsRemoteApi | getIntercomSettings | GET | /api/v1/intercoms/settings | deviceId | Response body not typed |
| IntercomsRemoteApi | updateIntercomSettings | PUT | /api/v1/intercoms/settings | deviceId, body | Response body not typed |
| NewsRemoteAPI | getNewsFeed | GET | /api/v1/newsproposals/feed | projectId, page, pageSize | NewsFeedItemDTO |
| NewsRemoteAPI | getNewsList | GET | /api/v1/newsproposals/news | projectId, isShownOnMain, page, pageSize | NewsItemDTO |
| OffersRemoteAPI | getOffersList | GET | /api/v1/newsproposals/proposals | projectId, isShownOnMain, page, pageSize | OffersItemDTO |
| NotificationsApi | registerToken | POST | /api/v1/notifications/devices | body | lbg |
| NotificationRemoteAPI | markAllUnread | POST | /api/v1/notifications/inApp/read | projectId, typeAlias | Response body not typed |
| NotificationRemoteAPI | readNotification | PUT | /api/v1/notifications/inApp/read/{id} | id | Response body not typed |
| NotificationRemoteAPI | getUnreadNotificationCount | GET | /api/v1/notifications/inApp/unreadCount | projectId | Response body not typed |
| NotificationsApi | markPushAsRead | PUT | /api/v1/notifications/push/read/{pushId} | pushId | lbg |
| NotificationsApi | resetUnreadPushCount | PUT | /api/v1/notifications/push/reset | none | lbg |
| PrivilegesApi | getPrivilegeDetail | GET | /api/v1/privileges/{id} | id | Response body not typed |
| PrivilegesApi | getClasses | GET | /api/v1/privileges/classes | none | Response body not typed |
| PrivilegesApi | putPersonalOffers | PUT | /api/v1/privileges/classes/personalOffers | body | Response body not typed |
| PrivilegesApi | getInterests | GET | /api/v1/privileges/interests | none | Response body not typed |
| PrivilegesApi | putInterests | PUT | /api/v1/privileges/interests | body | Response body not typed |
| PrivilegesApi | getInterestsSelected | GET | /api/v1/privileges/interests/selected | none | Response body not typed |
| PublicPlacesRemoteApi | getPublicPlacesList | GET | /api/v1/publicPlaces/ | projectId, typeAlias | Response body not typed |
| PublicPlacesRemoteApi | getPublicPlaceById | GET | /api/v1/publicPlaces/{id} | id | Response body not typed |
| PublicPlacesRemoteApi | getPublicPlacesTypes | GET | /api/v1/publicPlaces/types | projectId | Response body not typed |
| RemoteRequestsAPI | getRequestCommentsList | GET | /api/v1/requests/{id}/comments | id, page, pageSize | ChatCommentDTO |
| RemoteRequestsAPI | createRequestComment | POST | /api/v1/requests/{id}/comments | id | Response body not typed |
| RemoteRequestsAPI | getPassCategories | GET | /api/v1/requests/categories | projectId | Response body not typed |
| RemoteRequestsAPI | getActiveRequestsCount | GET | /api/v1/requests/counts | projectId | Response body not typed |
| RemoteRequestsAPI | getRateParams | GET | /api/v1/requests/rateParameters | none | Response body not typed |
| UpdateInfoRemoteAPI | getUpdateInfo | GET | /api/v1/staticData/update | deviceId | Response body not typed |
| UserProjectsRemoteApi | getUserProjects | GET | /api/v1/users/me/projects | none | Response body not typed |
| UserProjectsRemoteApi | getFeaturesForProject | GET | /api/v1/users/projects/{projectId}/features | projectId | Response body not typed |
| PrivilegesApi | getEvents | GET | /api/v2/activities/club/events | page, pageSize | k85 |
| PrivilegesApi | getEventCard | GET | /api/v2/activities/club/events/{eventId} | eventId | Response body not typed |
| InvoicePaymentMethodsRemoteAPI | getInvoicePaymentMethods | GET | /api/v2/finances/invoices/{invoiceId}/paymentMethods | invoiceId | Response body not typed |
| NewsRemoteAPI | getNewsDetails | GET | /api/v2/newsproposals/news/{newsId} | newsId | Response body not typed |
| OffersRemoteAPI | getOffersDetail | GET | /api/v2/newsproposals/proposals/{proposalId} | proposalId | Response body not typed |
| RemoteRequestsAPI | getRequestsList | GET | /api/v2/requests | projectId, statusAlias, typeAlias, dateFrom, dateTo, premises, query, page, pageSize, payable | RequestItemDTO |
| RemoteRequestsAPI | rateRequest | POST | /api/v2/requests/{id}/feedback | id, body | Response body not typed |
| RemoteRequestsAPI | getQuickFilters | GET | /api/v2/requests/quickFilters | none | Response body not typed |
| RemoteRequestsAPI | getStatusesList | GET | /api/v2/requests/statuses | projectId, onlyActive | Response body not typed |
| RemoteRequestsAPI | getRequestsTypesList | GET | /api/v2/requests/types | projectId, onlyActive, onlyShownOnMain | Response body not typed |
| CountersRemoteAPI | getCounters | GET | /api/v3/counters | projectId, premiseId, onlyAvailable | Response body not typed |
| InvoicesRemoteAPI | getPaymentLink | POST | /api/v3/finances/payment/acquiring | body | Response body not typed |
| PrivilegesApi | getInfo | GET | /api/v3/privileges/info | none | Response body not typed |
| RemoteRequestsAPI | getRequestDetails | GET | /api/v3/requests/{id} | id | Response body not typed |
| RemoteRequestsAPI | createPassRequest | POST | /api/v3/requests/pass | none | Response body not typed |
| RemoteRequestsAPI | createServiceRequest | POST | /api/v3/requests/service | none | Response body not typed |
| InvoicesRemoteAPI | getInvoicesPage | GET | /api/v4/finances/invoices | projectId, personalAccountId, merchantId, customerId, premiseId, invoiceTypeAlias, periodFrom, periodTo, isPaid, query, page, pageSize | pg7 |
| NotificationRemoteAPI | getDeepLink | POST | /api/v4/notifications/deeplink | body | Response body not typed |
| NotificationRemoteAPI | getNotificationList | GET | /api/v4/notifications/inApp | projectId, typeAlias, page, pageSize, onlyUnread | Response body not typed |
| OTPRemoteAPI | getOtpByEmail | POST | api/v1/auth/send | email | OtpResponse |
| OTPRemoteAPI | getOtpByPhone | POST | api/v1/auth/send | phone_number | OtpResponse |
| SignInRemoteAPI | signInByEmail | POST | api/v1/auth/token | client_id, grant_type, code, email | LoginResponse |
| SignInRemoteAPI | signInByPhone | POST | api/v1/auth/token | client_id, grant_type, code, phone_number | LoginResponse |
| TokensRemoteAPI | refreshTokens | POST | api/v1/auth/token | client_id, grant_type, refresh_token | LoginResponse |
| UserInfoRemoteAPI | getUserInfo | GET | api/v1/auth/userinfo | none | Response body not typed |
| UserInfoRemoteAPI | getUserInfoResponse | GET | api/v1/auth/userinfo | none | UserInfoDTO |
| RemoteDealsApi | getPayments | GET | api/v1/deals/payments | none | Response body not typed |
| RemoteDealsApi | getPremiseInfo | GET | api/v1/deals/premises/{premiseId} | premiseId | Response body not typed |
| RemoteDealsApi | getDealDocuments | GET | api/v1/deals/premises/{premiseId}/documents | premiseId | Response body not typed |
| RemoteDealsApi | getPlanningFiles | GET | api/v1/deals/premises/{premiseId}/layouts | premiseId | Response body not typed |
| RemoteDealsApi | getPaymentSchedule | GET | api/v1/deals/premises/{premiseId}/paymentSchedule | premiseId | Response body not typed |
| RemoteDealsApi | getPriceDynamics | GET | api/v1/deals/premises/{premiseId}/priceDynamics | premiseId, dateFrom, dateTo | Response body not typed |
| RemoteDealsApi | getProjectsList | GET | api/v1/deals/projects | none | Response body not typed |
| RemoteDealsApi | getProjectInfo | GET | api/v1/deals/projects/{projectId} | projectId | Response body not typed |
| RemoteDealsApi | getProjectsInfo | GET | api/v1/deals/projects/info | none | Response body not typed |
| RemoteDealsApi | getProjectsSites | GET | api/v1/deals/projects/update | none | Response body not typed |
| DynamicsRemoteApi | getBuildingTimeLapse | GET | api/v1/dynamics/projects/{projectId}/buildingTimeLapse | projectId | Response body not typed |
| DynamicsRemoteApi | getWebCamsForProject | GET | api/v1/dynamics/projects/{projectId}/cameras | projectId | Response body not typed |
| DynamicsRemoteApi | getPhotoReportsForProject | GET | api/v1/dynamics/projects/{projectId}/photoReports | projectId | Response body not typed |
| RemoteDealsApi | getPhotoReports | GET | api/v1/dynamics/projects/{projectId}/photoReports | projectId | Response body not typed |
| DynamicsRemoteApi | getVideoReportsForProject | GET | api/v1/dynamics/projects/{projectId}/videoReports | projectId | Response body not typed |
| PushSettingsApi | getPushSettings | GET | api/v1/notifications/push/settings | module | Response body not typed |
| PushSettingsApi | changePushSettings | PUT | api/v1/notifications/push/settings | body | wid |
| StaticDataRemoteAPI | getBasicInfo | GET | api/v1/staticData/basicinfo | none | Response body not typed |
| StaticDataRemoteAPI | getClubBasicInfo | GET | api/v1/staticData/club/basicInfo | none | Response body not typed |
| DocumentRemoteApi | getDocumentLink | GET | api/v1/staticData/documents/{id} | id | Response body not typed |
| InstructionRemoteApi | getInstructionTypes | GET | api/v1/staticData/instructionTypes | projectId | Response body not typed |
| StoriesRemoteAPI | getStoriesList | GET | api/v1/stories | projectId, module | Response body not typed |
| StoriesRemoteAPI | getStoryDetails | GET | api/v1/stories/{id} | id | Response body not typed |
| ContactsRemoteAPI | getContactsList | GET | api/v1/users/contacts | projectId, page, pageSize | b03 |
| ContactsRemoteAPI | closeAccess | DELETE | api/v1/users/contacts/{accountId} | accountId | lbg |
| ContactsRemoteAPI | getContactDetails | GET | api/v1/users/contacts/{accountId} | accountId | Response body not typed |
| UserPermissionsRemoteApi | getUserPermissions | GET | api/v1/users/me/permissions | none | Response body not typed |
| ProfileApi | deleteAvatar | DELETE | api/v1/users/profile/avatar | none | Response body not typed |
| ProfileApi | uploadAvatar | PUT | api/v1/users/profile/avatar | none | Response body not typed |
| DocumentRemoteApi | getDocuments | GET | api/v2/staticData/documents | projectId, typeAlias, query | Response body not typed |

Total Retrofit operations found: 104.

## Observed Android traffic for KAN-2

The Android `OkHttp` log captured during the KAN-2 Home-screen run confirms the
following calls after a successful OTP login:

- `GET /api/v1/auth/userinfo`
- `GET /api/v2/deals/projects/info`
- `GET /api/v2/stories?projectId=<id>&module=CLUB`
- `GET /api/v1/dynamics/projects/<id>/photoReports`
- `PUT /api/v1/notifications/push/reset`

`/api/v2/deals/projects/info` is now covered by the KAN-2 API review tests.
The contact-manager card itself did not cause a separate API call before it was
pressed, so no contact-manager endpoint is inferred from the captured traffic.

## Confidence and missing contract data

- HTTP methods, paths, form/query/path parameter names and top-level Retrofit DTO names are extracted from the APK and can be used for WireMock matching.
- Exact JSON schemas for every non-auth DTO, headers, pagination defaults, error bodies and required request-body fields need OpenAPI or captured test-environment traffic before creating reusable mappings.
- Do not route a production build to WireMock. Use a mock/debug build with an injectable API base URL.
