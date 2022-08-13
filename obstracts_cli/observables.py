"""
`Observable` class represents the properties of a given observable.
"""

import re
import pycountry
import validators
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface
from stix2 import ExternalReference, Indicator, Location, Vulnerability


class Observable:
    name = None
    name_delimeter = ": "
    type = None
    pattern = None  # Valid for indicators
    extraction_regex = None
    extraction_function = None

    def __init__(self, extracted_observable_text):
        self.extracted_observable_text = extracted_observable_text

    @property
    def pretty_name(self):
        return self.name

    @classmethod
    def extract_observables_from_text(cls, text):
        extracted_observables = []

        # If extraction_regex is not None, then find all matches to the regular expression
        if cls.extraction_regex != None:
            if cls.extraction_regex.startswith("^") and cls.extraction_regex.endswith(
                "$"
            ):
                # If regex starts with "^" and ends with "$", it's treated specially.
                # We iterate over each word and see if the regex exactly matches the word.
                # The drawback of this approach is that such regexes shouldn't contain
                # whitespaces.
                for word in text.split():
                    if re.match(cls.extraction_regex, word):
                        extracted_observables.append(cls(word))
            else:
                # Find regex in the entire text (including whitespace)
                for match in re.finditer(cls.extraction_regex, text):
                    extracted_observables.append(cls(match.group()))

        # If extraction_function is not None, then find matches that don't throw exception when
        # `pattern` function runs
        elif cls.extraction_function != None:
            for word in text.split():
                try:
                    if cls.extraction_function(word):
                        extracted_observables.append(cls(word))
                except Exception as error:
                    pass

        else:
            raise ValueError(
                "Both extraction_regex and extraction_function can't be None."
            )

        return extracted_observables

    def get_sdo_object(self):
        # By default, indicator SDO objects are created.
        if self.type == "indicator":
            if self.pattern == None:
                raise ValueError("pattern cannot be None for indicators.")

            # Replace extracted_observable_text placeholder
            pattern = self.pattern.format(
                extracted_observable_text=self.extracted_observable_text
            )

            # Escape '\' in pattern
            # https://github.com/oasis-open/cti-python-stix2/issues/260
            pattern = pattern.replace("\\", "\\\\")

            indicator = Indicator(
                type="indicator",
                name=f"{self.name}{self.name_delimeter}{self.extracted_observable_text}",
                pattern_type="stix",
                pattern=pattern,
                indicator_types=["malicious-activity"],
            )
            return indicator
        else:
            raise ValueError("Observable type is not supported")


class IPv4Observable(Observable):
    name = "ipv4"
    type = "indicator"
    pattern = "[ ipv4-addr:value = '{extracted_observable_text}' ]"
    extraction_function = lambda x: IPv4Interface(x)


class IPv4WithPortObservable(Observable):
    name = "ipv4"
    type = "indicator"
    pattern = "[ ipv4-addr:value = '{extracted_ip_address}' AND network-traffic:dst_port = '{extracted_ip_port}' ]"
    extraction_function = lambda x: IPv4WithPortObservable.validate_ipv4_with_port(x)

    @property
    def pretty_name(self):
        return "ipv4-with-port"

    # Helper function to validate ipv4 addresses with ports
    @staticmethod
    def validate_ipv4_with_port(x):
        if ":" in x:
            ip_address, port = x.split(":")

            # Validate ipv4 address part
            IPv4Address(ip_address)

            # Validate port part
            if 1 <= int(port) <= 65535:
                return ip_address, port

        return False

    def get_sdo_object(self):
        if self.type == "indicator":
            if self.pattern == None:
                raise ValueError("pattern cannot be None for indicators.")

            # Replace extracted_ip_address and extracted_ip_port placeholder
            ip_address, port = IPv4WithPortObservable.validate_ipv4_with_port(
                self.extracted_observable_text
            )
            pattern = self.pattern.format(
                extracted_ip_address=ip_address, extracted_ip_port=port
            )

            indicator = Indicator(
                type="indicator",
                name=f"{self.name}: {self.extracted_observable_text}",
                pattern_type="stix",
                pattern=pattern,
                indicator_types=["malicious-activity"],
            )
            return indicator
        else:
            raise ValueError("Observable type is not supported")


class IPv6Observable(Observable):
    name = "ipv6"
    type = "indicator"
    pattern = "[ ipv6-addr:value = '{extracted_observable_text}' ]"
    extraction_function = lambda x: IPv6Interface(x)


class IPv6WithPortObservable(Observable):
    name = "ipv6"
    type = "indicator"
    pattern = "[ ipv6-addr:value = '{extracted_ip_address}' AND network-traffic:dst_port = '{extracted_ip_port}' ]"
    extraction_function = lambda x: IPv6WithPortObservable.validate_ipv6_with_port(x)

    @property
    def pretty_name(self):
        return "ipv6-with-port"

    # Helper function to validate ipv4 addresses with ports
    @staticmethod
    def validate_ipv6_with_port(x):
        if ":" in x:
            ip_address, port = re.search(r"\[(.*)\]:(.*)", x).groups()

            # Validate ipv6 address part
            IPv6Address(ip_address)

            # Validate port part
            if 1 <= int(port) <= 65535:
                return ip_address, port

        return False

    def get_sdo_object(self):
        if self.type == "indicator":
            if self.pattern == None:
                raise ValueError("pattern cannot be None for indicators.")

            # Replace extracted_ip_address and extracted_ip_port placeholder
            ip_address, port = IPv6WithPortObservable.validate_ipv6_with_port(
                self.extracted_observable_text
            )
            pattern = self.pattern.format(
                extracted_ip_address=ip_address, extracted_ip_port=port
            )

            indicator = Indicator(
                type="indicator",
                name=f"{self.name}: {self.extracted_observable_text}",
                pattern_type="stix",
                pattern=pattern,
                indicator_types=["malicious-activity"],
            )
            return indicator
        else:
            raise ValueError("Observable type is not supported")


class FileNameObservable(Observable):
    name = "File name"
    type = "indicator"
    pattern = "[ file:name = '{extracted_observable_text}' ]"

    # Suspicious file extensions
    file_extensions = "(?:(?:7(?:Z|z))|(?:AP(?:K|P))|(?:B(?:AT|IN|MP))|(?:C(?:LASS|AB|ER|GI|HM|MD|RX))|(?:D(?:OCX?|EB|LL))|EXE|FLV|(?:G(?:ADGET|IF|Z))|INF|(?:J(?:A(?:VA|R)|PG|S))|(?:L(?:NK|OG))|(?:M(?:O(?:F|V)|P(?:4|G)|S(?:G|I)|4V))|ODT|(?:P(?:LUGIN|PTX?|7S|DF|HP|NG|SD|F|Y))|(?:R(?:AR|PM))|(?:S(?:VG|WF|YS|O))|(?:T(?:IFF?|AR|GZ|MP|XT))|(?:V(?:BS|IR))|(?:W(?:MV|SF))|XLSX?|ZIPX?|(?:ap(?:k|p))|(?:b(?:at|in|mp))|(?:c(?:lass|ab|er|gi|hm|md|rx))|(?:d(?:ocx?|eb|ll))|exe|flv|(?:g(?:adget|if|z))|inf|(?:j(?:a(?:va|r)|pg|s))|(?:l(?:nk|og))|(?:m(?:o(?:f|v)|p(?:4|g)|s(?:g|i)|4v))|odt|(?:p(?:lugin|ptx?|7s|df|hp|ng|sd|f|y))|(?:r(?:ar|pm))|(?:s(?:vg|wf|ys|o))|(?:t(?:iff?|ar|gz|mp|xt))|(?:v(?:bs|ir))|(?:w(?:mv|sf))|xlsx?|zipx?)"
    extraction_regex = rf"^(.*)\.({file_extensions})$"


class FileHashMD5Observable(Observable):
    name = "md5"
    type = "indicator"
    pattern = "[ file:hash.md5 = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.md5(x)


class FileHashSHA1Observable(Observable):
    name = "sha1"
    type = "indicator"
    pattern = "[ file:hash.sha1 = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.sha1(x)


class FileHashSHA256Observable(Observable):
    name = "sha256"
    type = "indicator"
    pattern = "[ file:hash.sha256 = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.sha256(x)


class FileHashSHA512Observable(Observable):
    name = "sha512"
    type = "indicator"
    pattern = "[ file:hash.sha512 = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.sha512(x)


class FileHashSsDeepObservable(Observable):
    name = "ssdeep"
    type = "indicator"
    pattern = "[ file:hash.ssdeep = '{extracted_observable_text}' ]"
    extraction_regex = r"^\d{1,}:[A-Za-z0-9/+]{3,}:[A-Za-z0-9/+]{3,}$"


class DirectoryPathObservable(Observable):
    name = "Directory"
    type = "indicator"
    pattern = "[ directory:path = '{extracted_observable_text}' ]"

    # Windows and Unix path
    windows_path = r"[A-Z]:(\\\\[^<>:\"/\\|\?\*]+)+"
    unix_path = r"(/\S+)+"
    extraction_regex = rf"^(({windows_path})|({unix_path}))$"


class DomainNameObservable(Observable):
    name = "Domain"
    type = "indicator"
    pattern = "[ domain-name:value = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.domain(x)


class UrlObservable(Observable):
    name = "URL"
    type = "indicator"
    pattern = "[ url:value = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.url(x)


class EmailAddressObservable(Observable):
    name = "Email Address"
    type = "indicator"
    pattern = "[ email-addr:value = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.email(x)


class MacAddressObservable(Observable):
    name = "MAC Address"
    type = "indicator"
    pattern = "[ mac-addr:value = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.mac_address(x)


class WindowsRegistryKeyObservable(Observable):
    name = "Windows Registry Key"
    type = "indicator"
    pattern = "[ windows-registry-key:key = '{extracted_observable_text}' ]"

    # Registry key
    registry_key = r"(?:CLSID|(?:HK(?:EY\_(?:CURRENT\_(?:CONFIG|USER)|LOCAL\_MACHINE|USERS)|C(?:C|U)|LM|U))|(?:I(?:nterface|ID))|REGISTRY|TypeLib)"
    extraction_regex = rf"^({registry_key}(\\[^<>:\"/\\|\?\*]+)+)$"


class UserAgentObservable(Observable):
    name = "User Agent"
    type = "indicator"
    pattern = "[ network-traffic:extensions.'http-requestext'.request_header.'User-Agent' = '{extracted_observable_text}' ]"

    # User agent
    platforms = r"([a-zA-Z]+)"
    user_agent_details = r"\([\w;\s\,.:-]+\)"
    user_agent = rf"((User-Agent: )|(user-agent: ))?Mozilla/5.0([ ](({user_agent_details})|(({platforms}/)\S+)))+"
    extraction_regex = rf"({user_agent})"


class AutonomousSystemNumberObservable(Observable):
    name = "AS"
    name_delimeter = ""
    type = "indicator"
    pattern = "[ autonomous-system:number = '{extracted_observable_text}' ]"
    extraction_regex = r"^((ASN?)\d+)$"


class CryptocurrencyBTCObservable(Observable):
    name = "BTC"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.btc_address(x)


class CryptocurrencyETHObservable(Observable):
    name = "ETH"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_regex = r"^(0x[a-f0-9]{40})$"


class CryptocurrencyXMRObservable(Observable):
    name = "XMR"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_regex = r"^(4[0-9AB][1-9A-HJ-NP-Za-km-z]{93})$"


class CVEObservale(Observable):
    name = "CVE"
    type = "vulnerability"
    extraction_regex = r"^(CVE-(19|20)\d{2}-\d{4,7})$"

    def get_sdo_object(self):
        vulnerability = Vulnerability(
            name=self.extracted_observable_text,
            external_references=ExternalReference(
                source_name="cve", external_id=self.extracted_observable_text
            ),
        )
        return vulnerability


class CountryNameObservable(Observable):
    name = "Country Name"
    type = "location"

    # Country names
    all_country_names = [country.name for country in pycountry.countries]
    extraction_regex = r"(" + r")|(".join(all_country_names) + r")"

    def get_sdo_object(self):
        # Find country iso
        country_iso = self.extracted_observable_text
        country = pycountry.countries.get(name=self.extracted_observable_text)
        if country != None:
            country_iso = country.alpha_2

        location = Location(
            name=f"{self.extracted_observable_text}", country=country_iso
        )
        return location


class CountryCodeAlpha2Observable(Observable):
    name = "Country Code Alpha 2"
    type = "location"

    # Country names
    all_country_names_alpha_2 = [country.alpha_2 for country in pycountry.countries]
    extraction_regex = r"(\s" + r"\s)|(\s".join(all_country_names_alpha_2) + r"\s)"

    def get_sdo_object(self):
        # TODO: This is a hack, think of a neater approach
        # Strip leading and trailing spaces
        extracted_observable_text = self.extracted_observable_text.strip()

        location = Location(
            name=f"{extracted_observable_text}", country=extracted_observable_text
        )
        return location


class CountryCodeAlpha3Observable(Observable):
    name = "Country Code Alpha 3"
    type = "location"

    # Country names
    all_country_names_alpha_3 = [country.alpha_3 for country in pycountry.countries]
    extraction_regex = r"(\s" + r"\s)|(\s".join(all_country_names_alpha_3) + r"\s)"

    def get_sdo_object(self):
        # TODO: This is a hack, think of a neater approach
        # Strip leading and trailing spaces
        extracted_observable_text = self.extracted_observable_text.strip()

        # Find country iso
        country_iso = extracted_observable_text
        country = pycountry.countries.get(alpha_3=extracted_observable_text)
        if country != None:
            country_iso = country.alpha_2

        location = Location(
            name=f"{extracted_observable_text}", country=country_iso
        )
        return location

class MastercardCreditCardObservable(Observable):
    name = "Mastercard Credit Card"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.mastercard(x)

class VisaCreditCardObservable(Observable):
    name = "VISA Credit Card"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.visa(x)

class AmexCreditCardObservable(Observable):
    name = "Amex Credit Card"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.amex(x)

class UnionPayCreditCardObservable(Observable):
    name = "Union Pay Credit Card"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.unionpay(x)

class DinersCreditCardObservable(Observable):
    name = "Diners Credit Card"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.diners(x)

class JCBCreditCardObservable(Observable):
    name = "JCB Credit Card"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.jcb(x)

class IBANCodeObservable(Observable):
    name = "IBAN"
    type = "indicator"
    pattern = "[ artifact:payload_bin = '{extracted_observable_text}' ]"
    extraction_function = lambda x: validators.iban(x)