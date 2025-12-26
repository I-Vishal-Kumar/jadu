import { FC } from "react";
import { Check } from "lucide-react";

interface StepperProps {
    currentStep: number;
    totalSteps: number;
    steps: string[];
}

const Stepper: FC<StepperProps> = ({ currentStep, totalSteps, steps }) => {
    return (
        <div className="w-full py-4">
            <div className="flex items-center justify-between max-w-5xl mx-auto px-4">
                {steps.map((step, index) => {
                    const stepNumber = index + 1;
                    const isActive = stepNumber === currentStep;
                    const isCompleted = stepNumber < currentStep;

                    return (
                        <div key={index} className="flex flex-col items-center flex-1 relative">
                            {/* Line connecting steps */}
                            {index !== 0 && (
                                <div
                                    className={`absolute top-5 -left-1/2 w-full h-[2px] -translate-y-1/2 transition-colors duration-500 ${isCompleted || isActive ? "bg-purple-600" : "bg-gray-200"
                                        }`}
                                />
                            )}

                            <div className="relative z-10 flex flex-col items-center">
                                <div
                                    className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${isCompleted
                                            ? "bg-purple-600 border-purple-600 text-white"
                                            : isActive
                                                ? "bg-white border-purple-600 text-purple-600 shadow-md scale-110"
                                                : "bg-white border-gray-200 text-gray-400"
                                        }`}
                                >
                                    {isCompleted ? (
                                        <Check className="w-6 h-6" />
                                    ) : (
                                        <span className="text-sm font-bold">{stepNumber}</span>
                                    )}
                                </div>
                                <span
                                    className={`absolute -bottom-6 text-[10px] font-semibold uppercase tracking-wider whitespace-nowrap transition-colors duration-500 ${isActive ? "text-purple-600" : "text-gray-400"
                                        }`}
                                >
                                    {step}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default Stepper;
