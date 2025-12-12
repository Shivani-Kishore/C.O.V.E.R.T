import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    is_valid: bool
    commitment: Optional[str] = None
    nullifier_hash: Optional[str] = None
    error: Optional[str] = None


class ZKProofVerifier:
    def __init__(self, verification_key_path: Optional[str] = None):
        if verification_key_path is None:
            circuits_dir = Path(__file__).parent.parent.parent.parent / "circuits"
            verification_key_path = str(circuits_dir / "verification_key.json")

        self.verification_key_path = verification_key_path
        self.verification_key = self._load_verification_key()

    def _load_verification_key(self) -> Optional[Dict]:
        try:
            with open(self.verification_key_path, 'r') as f:
                vkey = json.load(f)
            logger.info("Verification key loaded successfully")
            return vkey
        except FileNotFoundError:
            logger.warning(f"Verification key not found at {self.verification_key_path}")
            logger.warning("Run circuit setup script first: cd backend/circuits && ./setup.sh")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid verification key JSON: {e}")
            return None

    async def verify_proof(
        self,
        proof: Dict,
        public_signals: List[str]
    ) -> VerificationResult:
        if not self.verification_key:
            return VerificationResult(
                is_valid=False,
                error="Verification key not loaded. Run circuit setup first."
            )

        try:
            is_valid = await self._verify_with_snarkjs(proof, public_signals)

            if is_valid and len(public_signals) >= 2:
                return VerificationResult(
                    is_valid=True,
                    commitment=public_signals[0],
                    nullifier_hash=public_signals[1]
                )
            else:
                return VerificationResult(
                    is_valid=is_valid,
                    error="Invalid public signals" if not is_valid else None
                )

        except Exception as e:
            logger.error(f"Proof verification failed: {e}")
            return VerificationResult(
                is_valid=False,
                error=str(e)
            )

    async def _verify_with_snarkjs(
        self,
        proof: Dict,
        public_signals: List[str]
    ) -> bool:
        try:
            import tempfile
            import os

            with tempfile.TemporaryDirectory() as tmpdir:
                proof_path = os.path.join(tmpdir, "proof.json")
                public_path = os.path.join(tmpdir, "public.json")

                with open(proof_path, 'w') as f:
                    json.dump(proof, f)

                with open(public_path, 'w') as f:
                    json.dump(public_signals, f)

                result = subprocess.run(
                    [
                        "snarkjs",
                        "groth16",
                        "verify",
                        self.verification_key_path,
                        public_path,
                        proof_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 and "OK!" in result.stdout:
                    return True
                else:
                    logger.warning(f"Verification failed: {result.stdout}")
                    return False

        except subprocess.TimeoutExpired:
            logger.error("Proof verification timed out")
            return False
        except FileNotFoundError:
            logger.error("snarkjs not found. Install with: npm install -g snarkjs")
            return self._verify_with_python(proof, public_signals)
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False

    def _verify_with_python(self, proof: Dict, public_signals: List[str]) -> bool:
        try:
            from py_ecc.bn128 import pairing, G1, G2, add, multiply, neg
            from py_ecc.fields import bn128_FQ, bn128_FQ2

            pi_a = [
                G1(
                    (bn128_FQ(int(proof['pi_a'][0])), bn128_FQ(int(proof['pi_a'][1])))
                )
            ]

            pi_b = [
                G2(
                    (
                        bn128_FQ2([int(proof['pi_b'][0][0]), int(proof['pi_b'][0][1])]),
                        bn128_FQ2([int(proof['pi_b'][1][0]), int(proof['pi_b'][1][1])])
                    )
                )
            ]

            pi_c = [
                G1(
                    (bn128_FQ(int(proof['pi_c'][0])), bn128_FQ(int(proof['pi_c'][1])))
                )
            ]

            alpha_g1 = G1(
                (
                    bn128_FQ(int(self.verification_key['vk_alpha_1'][0])),
                    bn128_FQ(int(self.verification_key['vk_alpha_1'][1]))
                )
            )

            beta_g2 = G2(
                (
                    bn128_FQ2([
                        int(self.verification_key['vk_beta_2'][0][0]),
                        int(self.verification_key['vk_beta_2'][0][1])
                    ]),
                    bn128_FQ2([
                        int(self.verification_key['vk_beta_2'][1][0]),
                        int(self.verification_key['vk_beta_2'][1][1])
                    ])
                )
            )

            gamma_g2 = G2(
                (
                    bn128_FQ2([
                        int(self.verification_key['vk_gamma_2'][0][0]),
                        int(self.verification_key['vk_gamma_2'][0][1])
                    ]),
                    bn128_FQ2([
                        int(self.verification_key['vk_gamma_2'][1][0]),
                        int(self.verification_key['vk_gamma_2'][1][1])
                    ])
                )
            )

            delta_g2 = G2(
                (
                    bn128_FQ2([
                        int(self.verification_key['vk_delta_2'][0][0]),
                        int(self.verification_key['vk_delta_2'][0][1])
                    ]),
                    bn128_FQ2([
                        int(self.verification_key['vk_delta_2'][1][0]),
                        int(self.verification_key['vk_delta_2'][1][1])
                    ])
                )
            )

            vk_x = add(*[
                multiply(
                    G1(
                        (
                            bn128_FQ(int(ic[0])),
                            bn128_FQ(int(ic[1]))
                        )
                    ),
                    int(public_signals[i]) if i < len(public_signals) else 0
                )
                for i, ic in enumerate(self.verification_key['IC'])
            ])

            return (
                pairing(pi_b[0], pi_a[0]) ==
                pairing(beta_g2, alpha_g1) * pairing(gamma_g2, vk_x) * pairing(delta_g2, pi_c[0])
            )

        except ImportError:
            logger.warning("py_ecc not installed. Install with: pip install py_ecc")
            return False
        except Exception as e:
            logger.error(f"Python verification failed: {e}")
            return False

    def verify_nullifier_uniqueness(self, nullifier_hash: str, db_session) -> bool:
        from app.models.zkp_nullifier import ZKPNullifier

        existing = db_session.query(ZKPNullifier).filter_by(
            nullifier=nullifier_hash
        ).first()

        return existing is None

    def check_rate_limit(self, nullifier_hash: str, db_session) -> bool:
        from app.models.zkp_nullifier import ZKPNullifier
        from datetime import datetime, date

        nullifier = db_session.query(ZKPNullifier).filter_by(
            nullifier=nullifier_hash
        ).first()

        if nullifier is None:
            return True

        if nullifier.last_daily_reset < date.today():
            nullifier.daily_report_count = 0
            nullifier.last_daily_reset = date.today()
            db_session.commit()
            return True

        MAX_DAILY_REPORTS = 5
        return nullifier.daily_report_count < MAX_DAILY_REPORTS
