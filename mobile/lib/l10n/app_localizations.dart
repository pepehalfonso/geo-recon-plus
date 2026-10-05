import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es'),
  ];

  /// No description provided for @tagline.
  ///
  /// In en, this message translates to:
  /// **'IP geolocation & reputation'**
  String get tagline;

  /// No description provided for @statusNoKey.
  ///
  /// In en, this message translates to:
  /// **'Reputation via free DNS blocklists. Add an AbuseIPDB key for full reports.'**
  String get statusNoKey;

  /// No description provided for @statusHasKey.
  ///
  /// In en, this message translates to:
  /// **'AbuseIPDB key active: full reputation reports enabled.'**
  String get statusHasKey;

  /// No description provided for @inputLabel.
  ///
  /// In en, this message translates to:
  /// **'IP address or domain'**
  String get inputLabel;

  /// No description provided for @inputHint.
  ///
  /// In en, this message translates to:
  /// **'8.8.8.8'**
  String get inputHint;

  /// No description provided for @lookUp.
  ///
  /// In en, this message translates to:
  /// **'Look up'**
  String get lookUp;

  /// No description provided for @myIp.
  ///
  /// In en, this message translates to:
  /// **'My IP'**
  String get myIp;

  /// No description provided for @recent.
  ///
  /// In en, this message translates to:
  /// **'Recent'**
  String get recent;

  /// No description provided for @clear.
  ///
  /// In en, this message translates to:
  /// **'Clear'**
  String get clear;

  /// No description provided for @refresh.
  ///
  /// In en, this message translates to:
  /// **'Refresh'**
  String get refresh;

  /// No description provided for @sources.
  ///
  /// In en, this message translates to:
  /// **'Data: ipwho.is, ipify, Google DNS, Spamhaus / SpamCop / Barracudacentral.'**
  String get sources;

  /// No description provided for @settingsTitle.
  ///
  /// In en, this message translates to:
  /// **'AbuseIPDB API key'**
  String get settingsTitle;

  /// No description provided for @settingsHelp.
  ///
  /// In en, this message translates to:
  /// **'Optional. Without it the app uses free DNS blocklists only. Get one at abuseipdb.com.'**
  String get settingsHelp;

  /// No description provided for @apiKeyLabel.
  ///
  /// In en, this message translates to:
  /// **'API key'**
  String get apiKeyLabel;

  /// No description provided for @apiKeyHint.
  ///
  /// In en, this message translates to:
  /// **'paste your key'**
  String get apiKeyHint;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @copyIp.
  ///
  /// In en, this message translates to:
  /// **'Copy IP'**
  String get copyIp;

  /// No description provided for @copyJson.
  ///
  /// In en, this message translates to:
  /// **'Copy report as JSON'**
  String get copyJson;

  /// No description provided for @ipCopied.
  ///
  /// In en, this message translates to:
  /// **'IP copied'**
  String get ipCopied;

  /// No description provided for @jsonCopied.
  ///
  /// In en, this message translates to:
  /// **'JSON report copied'**
  String get jsonCopied;

  /// No description provided for @verdictClean.
  ///
  /// In en, this message translates to:
  /// **'CLEAN'**
  String get verdictClean;

  /// No description provided for @verdictSuspicious.
  ///
  /// In en, this message translates to:
  /// **'SUSPICIOUS'**
  String get verdictSuspicious;

  /// No description provided for @verdictMalicious.
  ///
  /// In en, this message translates to:
  /// **'MALICIOUS'**
  String get verdictMalicious;

  /// No description provided for @verdictUnknown.
  ///
  /// In en, this message translates to:
  /// **'UNKNOWN'**
  String get verdictUnknown;

  /// No description provided for @abuseConfidence.
  ///
  /// In en, this message translates to:
  /// **'Abuse confidence: {score}/100'**
  String abuseConfidence(Object score);

  /// No description provided for @reports.
  ///
  /// In en, this message translates to:
  /// **'Reports: {count}'**
  String reports(Object count);

  /// No description provided for @lastReported.
  ///
  /// In en, this message translates to:
  /// **'Last reported: {date}'**
  String lastReported(Object date);

  /// No description provided for @privateSection.
  ///
  /// In en, this message translates to:
  /// **'Non-public address'**
  String get privateSection;

  /// No description provided for @scope.
  ///
  /// In en, this message translates to:
  /// **'Scope'**
  String get scope;

  /// No description provided for @privateNote.
  ///
  /// In en, this message translates to:
  /// **'There is no public geolocation data for this address.'**
  String get privateNote;

  /// No description provided for @geoSection.
  ///
  /// In en, this message translates to:
  /// **'Geolocation'**
  String get geoSection;

  /// No description provided for @country.
  ///
  /// In en, this message translates to:
  /// **'Country'**
  String get country;

  /// No description provided for @region.
  ///
  /// In en, this message translates to:
  /// **'Region'**
  String get region;

  /// No description provided for @city.
  ///
  /// In en, this message translates to:
  /// **'City'**
  String get city;

  /// No description provided for @timezone.
  ///
  /// In en, this message translates to:
  /// **'Timezone'**
  String get timezone;

  /// No description provided for @coordinates.
  ///
  /// In en, this message translates to:
  /// **'Coordinates'**
  String get coordinates;

  /// No description provided for @networkSection.
  ///
  /// In en, this message translates to:
  /// **'Network'**
  String get networkSection;

  /// No description provided for @asn.
  ///
  /// In en, this message translates to:
  /// **'ASN'**
  String get asn;

  /// No description provided for @organization.
  ///
  /// In en, this message translates to:
  /// **'Organization'**
  String get organization;

  /// No description provided for @isp.
  ///
  /// In en, this message translates to:
  /// **'ISP'**
  String get isp;

  /// No description provided for @domain.
  ///
  /// In en, this message translates to:
  /// **'Domain'**
  String get domain;

  /// No description provided for @reverseDns.
  ///
  /// In en, this message translates to:
  /// **'Reverse DNS'**
  String get reverseDns;

  /// No description provided for @ipVersion.
  ///
  /// In en, this message translates to:
  /// **'Version'**
  String get ipVersion;

  /// No description provided for @unknown.
  ///
  /// In en, this message translates to:
  /// **'unknown'**
  String get unknown;

  /// No description provided for @none.
  ///
  /// In en, this message translates to:
  /// **'none'**
  String get none;

  /// No description provided for @sourceNote.
  ///
  /// In en, this message translates to:
  /// **'Source: {provider} · geolocation is an estimate, not a physical trace.'**
  String sourceNote(Object provider);

  /// No description provided for @openMap.
  ///
  /// In en, this message translates to:
  /// **'Open on map'**
  String get openMap;

  /// No description provided for @openMapFailed.
  ///
  /// In en, this message translates to:
  /// **'Could not open the map.'**
  String get openMapFailed;

  /// No description provided for @resolvedFrom.
  ///
  /// In en, this message translates to:
  /// **'Resolved from {host}'**
  String resolvedFrom(Object host);

  /// No description provided for @scopeLoopback.
  ///
  /// In en, this message translates to:
  /// **'loopback'**
  String get scopeLoopback;

  /// No description provided for @scopeLinkLocal.
  ///
  /// In en, this message translates to:
  /// **'link-local'**
  String get scopeLinkLocal;

  /// No description provided for @scopeDocumentation.
  ///
  /// In en, this message translates to:
  /// **'documentation'**
  String get scopeDocumentation;

  /// No description provided for @scopeCarrierGrade.
  ///
  /// In en, this message translates to:
  /// **'carrier-grade NAT'**
  String get scopeCarrierGrade;

  /// No description provided for @scopePrivate.
  ///
  /// In en, this message translates to:
  /// **'private'**
  String get scopePrivate;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
