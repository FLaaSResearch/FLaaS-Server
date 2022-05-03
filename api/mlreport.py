from sklearn import metrics


class MLReport:

    def __init__(self, y_true, y_pred):

        self.y_true = y_true
        self.y_pred = y_pred

    def get_report(self):
        return metrics.classification_report(self.y_true, self.y_pred)

    def get_accuracy(self):
        return metrics.accuracy_score(self.y_true, self.y_pred)

    def get_precision(self):
        return metrics.precision_score(self.y_true, self.y_pred)

    def get_f1_score(self):
        return metrics.f1_score(self.y_true, self.y_pred)
