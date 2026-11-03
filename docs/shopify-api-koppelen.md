# Shopify API koppelen (Dev Dashboard, client credentials)

Opgesteld 3 nov 2026. Getest op Suelta (`50134d.myshopify.com`): token, scopes en een GraphQL-call werken.
Sinds 1 jan 2026 kan een nieuwe winkel geen "legacy custom app" (`shpat_`-token) meer maken. Dit is de nieuwe route.

## Hoe het werkt
- Je maakt een **app** in het Dev Dashboard en installeert die op je winkel.
- De app heeft een **Client ID** en **Client secret** (`shpss_...`). Die blijven geldig zolang de app geinstalleerd is en je het secret niet vernieuwt.
- Een script ruilt die twee in voor een **access token**. Dat token is **24 uur geldig**, dus het script haalt bij elke run een nieuw token op (1 call, automatisch).
- Het secret is dus de blijvende sleutel. Behandel het als een wachtwoord.

## Per winkel: stappen

### 1. App aanmaken
1. Ga naar https://dev.shopify.com/dashboard en log in.
2. **Apps -> Create app**. Naam bijvoorbeeld "Claude scripts".
3. **App URL:** `https://shopify.dev/apps/default-app-home`. **Redirect URLs:** leeg laten, of `https://example.com/callback` als het verplicht is. **Embed app in Shopify admin:** uit.

### 2. Scopes kiezen en versie releasen
1. Open **Versions** en voeg de Admin API-scopes toe (komma-gescheiden, in een keer).
2. **Release** de versie. Een concept telt niet.

Scopes die we voor Suelta gebruikten (`write_` bevat `read_`):
```
read_products,write_products,read_product_listings,read_inventory,write_inventory,read_locations,read_orders,write_orders,read_draft_orders,write_draft_orders,read_customers,write_customers,read_fulfillments,write_fulfillments,read_assigned_fulfillment_orders,read_merchant_managed_fulfillment_orders,write_merchant_managed_fulfillment_orders,read_returns,write_returns,read_discounts,write_discounts,read_price_rules,write_price_rules,read_gift_cards,write_gift_cards,read_content,write_content,read_files,write_files,read_themes,write_themes,read_metaobjects,write_metaobjects,read_metaobject_definitions,write_metaobject_definitions,read_translations,write_translations,read_locales,write_locales,read_markets,write_markets,read_shipping,write_shipping,read_publications,write_publications,read_marketing_events,write_marketing_events,read_reports,read_analytics,read_checkouts,write_checkouts,read_shopify_payments_payouts
```
Minder is veiliger. Orders ouder dan 60 dagen vragen `read_all_orders` (Shopify moet dat goedkeuren). Klantgegevens in orders kunnen "protected customer data"-toegang vragen (Dev Dashboard -> API access).

### 3. Installeren
1. In de app: **Home -> Install app** (of **Select store**), kies de winkel.
2. Keur de rechten goed in de Shopify-admin. Dat doet de winkeleigenaar zelf.
3. Controleer: de app staat onder **Settings -> Apps and sales channels** van die winkel.

Wijzig je later scopes: nieuwe versie releasen en de app op de winkel **updaten**.

### 4. Gegevens verzamelen
- **Client ID** en **Client secret:** Dev Dashboard -> app -> **Settings**.
- **Winkeldomein:** in de adresbalk van de admin staat `admin.shopify.com/store/<naam>`. Dan is het domein `<naam>.myshopify.com` (niet het eigen domein zoals sueltajewelry.com).

### 5. In `.env` zetten (door de eigenaar, nooit in de chat)
Open `.env` in TextEdit (Finder: `Cmd+Shift+.` toont verborgen bestanden). Een blok per winkel (zie `.env.example`):
```
SHOPIFY_SHOP=50134d.myshopify.com
SHOPIFY_CLIENT_ID=...
SHOPIFY_CLIENT_SECRET=...
```
Meerdere winkels: gebruik een voorvoegsel, bijvoorbeeld `SHOPIFY_SUELTA_SHOP`, `SHOPIFY_CUPRIA_SHOP`, `SHOPIFY_ZOFIA_SHOP` (met `_CLIENT_ID` en `_CLIENT_SECRET` erachter). De bestaande Suelta-regels (zonder voorvoegsel) blijven werken: het hulpscript gebruikt die als je geen winkelnaam opgeeft.

Een app werkt alleen op winkels van dezelfde organisatie. Staan al je winkels onder een account, dan kun je dezelfde app installeren op elke winkel (zelfde Client ID en secret, andere `_SHOP`). Anders maak je per winkel een app.

### 6. Testen
Vraag Claude: "check Shopify voor <winkel>", of draai zelf:
```
python3 scripts/shopify_auth.py check           # regels zonder voorvoegsel
python3 scripts/shopify_auth.py check suelta    # SHOPIFY_SUELTA_*
```
Het script haalt een token op en vraagt winkelnaam en aantal producten op. Goed resultaat: `token ok` en de juiste winkelnaam.

## Foutmeldingen
| Melding | Betekenis | Oplossing |
|---|---|---|
| `app_not_installed` | App staat niet op deze winkel | Stap 3 doen (Install app) |
| `application_cannot_be_found` | Client ID klopt niet of hoort bij een andere organisatie | Client ID uit Settings opnieuw kopieren; winkel en app onder dezelfde organisatie |
| `invalid_client` / 401 | Client secret fout of vernieuwd | Secret opnieuw uit Settings in `.env` zetten |
| Scope ontbreekt (`access denied`) | Scope niet in de gereleasde versie | Scope toevoegen, nieuwe versie releasen, app updaten |

## Veiligheid
- Plak nooit een secret of token in de chat. Staat er toch een in: secret vernieuwen in Dev Dashboard -> Settings en `.env` bijwerken.
- `.env` nooit committen of delen (staat in `.gitignore`).
- Geef alleen de scopes die je nodig hebt.
