# Copyright 2019 VinyMeuh. All rights reserved.
# Use of the source code is governed by a MIT-style license that can be found in the LICENSE file.
import logging

from datetime import datetime
from dateutil.relativedelta import relativedelta
from ruamel.yaml import YAML, yaml_object

yaml = YAML(typ="safe")


@yaml_object(yaml)
class Loan:
    def __init__(self, name, revision, phases):
        self.name = name
        self.revision = revision
        self.phases = phases
        self.repayments = []
        self.early_repayments = []
        self.summary = {}

    def compute_repayment_plan(self):
        # re-initialize repayment plan
        self.repayments = []
        self.early_repayments = []

        for n, phase in enumerate(self.phases):
            # logging.debug("computing repayments for phase n° {}".format(n+1))
            logging.debug(f"computing repayments for phase n° {n+1}")

            # for_periods = duration of this phase
            if n < len(self.phases) - 1:
                d1 = datetime.strptime(phase["startDate"], "%Y-%m-%d")
                d2 = datetime.strptime(self.phases[n + 1]["startDate"], "%Y-%m-%d")
                for_periods = 12 * (d2.year - d1.year) + (d2.month - d1.month)
            else:
                for_periods = phase["periods"]
            logging.debug(f"  {'for_periods':24s} = {for_periods}")

            # Initialize previous_installment_date
            previous_repayment_date = datetime.strptime(phase["startDate"], "%Y-%m-%d")
            logging.debug(
                f"  {'previous_repayment_date':24s} = {previous_repayment_date}"
            )

            # Initialize previous_principal_after
            if n == 0:
                previous_principal_after = phase["principal"]
            else:
                if "principal" in phase:
                    if phase["principal"] < 0:  # Add an early repayment
                        self.early_repayments.append(
                            {
                                "date": phase["startDate"],
                                "repayment": -1 * phase["principal"],
                            }
                        )
                    previous_principal_after = (
                        phase["principal"] + self.repayments[-1]["principal_after"]
                    )
                else:
                    previous_principal_after = self.repayments[-1]["principal_after"]
            logging.debug(
                f"  {'previous_principal_after':24s} = {previous_principal_after}"
            )

            # Constants for current phase
            monthly_rate = phase["annualRate"] / 100 / 12
            logging.debug(f"  {'monthly_rate':24s} = {monthly_rate}")

            monthly_amount = round(
                (previous_principal_after * monthly_rate)
                / (1 - (1 + monthly_rate) ** (-1 * phase["periods"])),
                2,
            )
            logging.debug(f"  {'computed monthly_amount':24s} = {monthly_amount}")

            if "adjustment" in phase:
                logging.debug(f"  {'adjustment':24s} = {phase['adjustment']}")
                monthly_amount += phase["adjustment"]
                logging.debug(f"  {'corrected monthly_amount':24s} = {monthly_amount}")

            if "insurance" in phase:
                monthly_insurance = phase["insurance"]
            else:
                monthly_insurance = 0
            logging.debug(f"  {'monthly_insurance':24s} = {monthly_insurance}")

            for i in range(1, for_periods + 1):
                # Computes for current installment
                current_interest = round(previous_principal_after * monthly_rate, 2)
                current_repayment = round(
                    min(monthly_amount - current_interest, previous_principal_after), 2
                )
                current_principal_after = round(
                    previous_principal_after - current_repayment, 2
                )
                current_repayment_date = previous_repayment_date + relativedelta(
                    months=1
                )

                # Add new repayment to repayment plan
                repayment = {
                    "date": current_repayment_date.strftime("%Y-%m-%d"),
                    "amount": round(monthly_amount + monthly_insurance, 2),
                    "repayment": current_repayment,
                    "interest": current_interest,
                    "insurance": monthly_insurance,
                    "principal_after": current_principal_after,
                }
                self.repayments.append(repayment)

                # Prepare for next installment
                previous_repayment_date = current_repayment_date
                previous_principal_after = current_principal_after
            else:
                # Finished for this phase
                logging.debug(
                    f"  {'last principal_after':24s} = {self.repayments[-1]['principal_after']}"
                )
                pass

        # Correcting last repayment if needed
        if self.repayments[-1]["principal_after"] > 0:
            logging.debug("ultimate principal_after not equals zero => fix")
            self.repayments[-1]["repayment"] += self.repayments[-1]["principal_after"]
            self.repayments[-1]["interest"] -= self.repayments[-1]["principal_after"]
            self.repayments[-1]["principal_after"] = 0

        logging.debug("all phases have been computed successfully :)")
        logging.debug("calculation of the repayment summary")
        self._compute_summary()

    def _compute_summary(self):
        s_duration = 0
        s_interest = 0
        s_insurance = 0
        s_repayment = 0
        s_end_date = "0000-00-00"
        for repayment in self.repayments:
            s_duration += 1
            s_interest += repayment["interest"]
            s_insurance += repayment["insurance"]
            s_repayment += repayment["repayment"]
            s_end_date = max(s_end_date, repayment["date"])

        s_erepayment = 0
        for erepayment in self.early_repayments:
            s_erepayment += erepayment["repayment"]

        last_phase_amount = self.repayments[-1]["amount"]

        self.summary = {
            "duration": s_duration,
            "insurance": round(s_insurance, 2),
            "interest": round(s_interest, 2),
            "repayment": round(s_repayment, 2),
            "end_date": s_end_date,
            "early_repayment": round(s_erepayment, 2),
            "last_phase_amount": last_phase_amount,
        }

    def sanity_checks(self):
        healthy = True

        # duration
        if len(self.phases) == 1:
            e_duration = self.phases[0]["periods"]
        else:
            d1 = datetime.strptime(self.phases[0]["startDate"], "%Y-%m-%d")
            d2 = datetime.strptime(self.phases[-1]["startDate"], "%Y-%m-%d")
            e_duration = (
                12 * (d2.year - d1.year) + (d2.month - d1.month)
            ) + self.phases[-1]["periods"]
        c_duration = self.summary["duration"]
        if c_duration != e_duration:
            logging.warn(
                f"plan duration is not correct (expected={e_duration}, computed={c_duration})"
            )
            healthy = False

        # repayment is complete
        e_principal = self.phases[0]["principal"]
        c_principal = self.summary["repayment"] + self.summary["early_repayment"]
        if c_principal != e_principal:
            logging.warn(
                f"total repayment is not correct (expected={e_principal}, computed={c_principal})"
            )
            healthy = False

        # no remaining due
        e_last_principal_after = 0
        c_last_principal_after = self.repayments[-1]["principal_after"]
        if c_last_principal_after != e_last_principal_after:
            logging.warn(
                f"principal after last repayment not equals zero (expected={e_last_principal_after}, computed={c_last_principal_after})"
            )
            healthy = False

        return healthy
